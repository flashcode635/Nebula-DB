#!/usr/bin/env python3
"""
NebulaDB Interactive REPL Shell
--------------------------------
Priority #1 from the Day-2 improvement notes: keep the process (and the
WiredTiger connection / buffer pool) alive across commands, instead of
re-launching `python main.py ...` for every single operation, which was
tearing down the cache on every call.

Usage:
    python shell.py [db_name]

Example session:
    $ python shell.py
    Nebula DB v0.1 (WiredTiger Engine)
    nebula> CREATE COLLECTION users {"name":"string","age":"integer"}
    nebula> INSERT INTO users u1 {"name":"Ramit","age":22}
    nebula> READ users u1
    nebula> FIND IN users WHERE age > 20
    nebula> EXIT
"""

import sys
import json
import os
import time

from main import NeBulaDB

class Colors:
    """ANSI colors used by the interactive shell."""

    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    DIM = "\033[2m"
    WHITE = "\033[37m"
    BRIGHT_WHITE = "\033[97m"


BANNER = "Nebula DB v0.1 (WiredTiger Engine)\nType HELP for commands, EXIT or QUIT to leave.\n"

HELP_TEXT = """
Available commands:
  CREATE COLLECTION <name> <schema_json>
      e.g. CREATE COLLECTION users {"name":"string","age":"integer"}

  INSERT INTO <collection> <doc_id> <data_json>
      e.g. INSERT INTO users u1 {"name":"Ramit","age":22}

  READ <collection> <doc_id>
      e.g. READ users u1

  UPDATE <collection> <doc_id> <data_json>
      e.g. UPDATE users u1 {"name":"Ramit","age":23}

  DELETE <collection> <doc_id>
      e.g. DELETE users u1

  FIND IN <collection> WHERE <field> <op> <value>
      op is one of: = != > < >= <=
      e.g. FIND IN users WHERE age > 20

  STATS
      Show WiredTiger session stats handle info for this connection.

  HELP
      Show this message.

  EXIT / QUIT
      Flush, close the connection cleanly, and leave the shell.
"""

OPS = {
    "=":  lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">":  lambda a, b: a is not None and a > b,
    "<":  lambda a, b: a is not None and a < b,
    ">=": lambda a, b: a is not None and a >= b,
    "<=": lambda a, b: a is not None and a <= b,
}


def parse_json_arg(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {raw!r} ({e})")


def match_filter(document, field, op_symbol, value):
    return OPS[op_symbol](document.get(field), value)


class NebulaShell:
    def __init__(self, db_name="nebula_shell_db"):
        self.db_name = db_name
        self.db = None
        self.use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ

    def _color(self, text, color):
        if not self.use_color:
            return text
        return f"{color}{text}{Colors.RESET}"

    def _print_result(self, result):
        text = str(result)
        if text.startswith("Error:") or text.startswith("Could not"):
            color = Colors.RED
        elif "successfully" in text or text.startswith("Collection '"):
            color = Colors.GREEN
        elif text.startswith("No matching") or text.startswith("Unknown command"):
            color = Colors.YELLOW
        elif text.startswith("(") and "matched" in text:
            color = Colors.DIM
        else:
            color = Colors.BRIGHT_WHITE
        print(self._color(text, color))

    def start(self):
        print(self._color(BANNER, Colors.BRIGHT_WHITE))
        self.db = NeBulaDB(self.db_name)
        print(self._color(f"[connected] db='{self.db_name}'", Colors.GREEN), end=" ")
        print(self._color("WiredTiger connection open, session persists across commands.", Colors.DIM))
        try:
            self._loop()
        finally:
            if self.db:
                self.db.close()
                print("\n" + self._color("[closed]", Colors.GREEN), end=" ")
                print(self._color("WiredTiger connection & session terminated cleanly.", Colors.DIM))

    def _loop(self):
        while True:
            try:
                raw = input(self._color("nebula> ", Colors.CYAN)).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not raw:
                continue
            if raw.upper() in ("EXIT", "QUIT"):
                break

            try:
                self._dispatch(raw)
            except Exception as e:
                self._print_result(f"Error: {e}")

    def _dispatch(self, raw: str):
        upper = raw.upper()

        if upper == "HELP":
            for line in HELP_TEXT.splitlines():
                if not line:
                    print()
                elif line.startswith("  e.g.") or line.startswith("      "):
                    print(self._color(line, Colors.DIM))
                elif line.startswith("  "):
                    print(self._color(line, Colors.BLUE))
                else:
                    print(self._color(line, Colors.BRIGHT_WHITE))
        elif upper == "STATS":
            self._cmd_stats()
        elif upper.startswith("CREATE COLLECTION"):
            self._cmd_create(raw)
        elif upper.startswith("INSERT INTO"):
            self._cmd_insert(raw)
        elif upper.startswith("UPDATE"):
            self._cmd_update(raw)
        elif upper.startswith("DELETE"):
            self._cmd_delete(raw)
        elif upper.startswith("FIND IN"):
            self._cmd_find(raw)
        elif upper.startswith("READ"):
            self._cmd_read(raw)
        else:
            self._print_result(f"Unknown command: '{raw}'. Type HELP for usage.")

    # ---- command handlers -------------------------------------------------

    def _cmd_create(self, raw: str):
        tokens = raw.split(None, 3)  # CREATE COLLECTION <name> <schema_json>
        if len(tokens) < 4:
            raise ValueError("Usage: CREATE COLLECTION <name> <schema_json>")
        _, _, name, schema_json = tokens
        schema = parse_json_arg(schema_json)
        self._print_result(self.db.create_collection(name, schema))

    def _cmd_insert(self, raw: str):
        tokens = raw.split(None, 4)  # INSERT INTO <collection> <doc_id> <data_json>
        if len(tokens) < 5:
            raise ValueError("Usage: INSERT INTO <collection> <doc_id> <data_json>")
        _, _, coll, doc_id, data_json = tokens
        data = parse_json_arg(data_json)
        self._print_result(self.db.insert(coll, doc_id, data))

    def _cmd_update(self, raw: str):
        tokens = raw.split(None, 3)  # UPDATE <collection> <doc_id> <data_json>
        if len(tokens) < 4:
            raise ValueError("Usage: UPDATE <collection> <doc_id> <data_json>")
        _, coll, doc_id, data_json = tokens
        data = parse_json_arg(data_json)
        self._print_result(self.db.update(coll, doc_id, data))

    def _cmd_delete(self, raw: str):
        tokens = raw.split()  # DELETE <collection> <doc_id>
        if len(tokens) != 3:
            raise ValueError("Usage: DELETE <collection> <doc_id>")
        _, coll, doc_id = tokens
        self._print_result(self.db.delete(coll, doc_id))

    def _cmd_read(self, raw: str):
        tokens = raw.split()  # READ <collection> <doc_id>
        if len(tokens) != 3:
            raise ValueError("Usage: READ <collection> <doc_id>")
        _, coll, doc_id = tokens
        self._print_result(self.db.read(coll, doc_id))

    def _cmd_find(self, raw: str):
        # FIND IN <collection> WHERE <field> <op> <value>
        tokens = raw.split(None, 6)
        if len(tokens) < 7 or tokens[3].upper() != "WHERE":
            raise ValueError("Usage: FIND IN <collection> WHERE <field> <op> <value>")

        coll, field, op_symbol, value_raw = tokens[2], tokens[4], tokens[5], tokens[6]

        if op_symbol not in OPS:
            raise ValueError(f"Unsupported operator '{op_symbol}'. Use one of: {', '.join(OPS)}")

        try:
            value = json.loads(value_raw)
        except json.JSONDecodeError:
            value = value_raw  # fall back to treating it as a raw string

        if coll not in self.db.collections:
            self._print_result("Error: Collection not found.")
            return

        start = time.perf_counter()
        results = [doc for doc in self.db.collections[coll] if match_filter(doc, field, op_symbol, value)]
        elapsed_ms = (time.perf_counter() - start) * 1000

        if not results:
            self._print_result("No matching documents.")
        else:
            for doc in results:
                print(self._color(doc, Colors.CYAN))
        print(self._color(f"({len(results)} matched, full scan in {elapsed_ms:.2f}ms)", Colors.DIM))

    def _cmd_stats(self):
        try:
            stats = self.db.cache.get_stats()
            print(self._color("WiredTiger session stats cursor acquired.", Colors.BLUE))
            print(self._color(stats, Colors.MAGENTA))
        except Exception as e:
            self._print_result(f"Could not fetch stats: {e}")


def main():
    db_name = sys.argv[1] if len(sys.argv) > 1 else "nebula_shell_db"
    NebulaShell(db_name=db_name).start()


if __name__ == "__main__":
    main()