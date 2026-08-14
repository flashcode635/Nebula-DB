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
import time

from main import NeBulaDB

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

    def start(self):
        print(BANNER)
        self.db = NeBulaDB(self.db_name)
        print(f"[connected] db='{self.db_name}' — WiredTiger connection open, session persists across commands.")
        try:
            self._loop()
        finally:
            if self.db:
                self.db.close()
                print("\n[closed] WiredTiger connection & session terminated cleanly.")

    def _loop(self):
        while True:
            try:
                raw = input("nebula> ").strip()
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
                print(f"Error: {e}")

    def _dispatch(self, raw: str):
        upper = raw.upper()

        if upper == "HELP":
            print(HELP_TEXT)
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
            print(f"Unknown command: '{raw}'. Type HELP for usage.")

    # ---- command handlers -------------------------------------------------

    def _cmd_create(self, raw: str):
        tokens = raw.split(None, 3)  # CREATE COLLECTION <name> <schema_json>
        if len(tokens) < 4:
            raise ValueError("Usage: CREATE COLLECTION <name> <schema_json>")
        _, _, name, schema_json = tokens
        schema = parse_json_arg(schema_json)
        print(self.db.create_collection(name, schema))

    def _cmd_insert(self, raw: str):
        tokens = raw.split(None, 4)  # INSERT INTO <collection> <doc_id> <data_json>
        if len(tokens) < 5:
            raise ValueError("Usage: INSERT INTO <collection> <doc_id> <data_json>")
        _, _, coll, doc_id, data_json = tokens
        data = parse_json_arg(data_json)
        print(self.db.insert(coll, doc_id, data))

    def _cmd_update(self, raw: str):
        tokens = raw.split(None, 3)  # UPDATE <collection> <doc_id> <data_json>
        if len(tokens) < 4:
            raise ValueError("Usage: UPDATE <collection> <doc_id> <data_json>")
        _, coll, doc_id, data_json = tokens
        data = parse_json_arg(data_json)
        print(self.db.update(coll, doc_id, data))

    def _cmd_delete(self, raw: str):
        tokens = raw.split()  # DELETE <collection> <doc_id>
        if len(tokens) != 3:
            raise ValueError("Usage: DELETE <collection> <doc_id>")
        _, coll, doc_id = tokens
        print(self.db.delete(coll, doc_id))

    def _cmd_read(self, raw: str):
        tokens = raw.split()  # READ <collection> <doc_id>
        if len(tokens) != 3:
            raise ValueError("Usage: READ <collection> <doc_id>")
        _, coll, doc_id = tokens
        print(self.db.read(coll, doc_id))

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
            print("Error: Collection not found.")
            return

        start = time.perf_counter()
        results = [doc for doc in self.db.collections[coll] if match_filter(doc, field, op_symbol, value)]
        elapsed_ms = (time.perf_counter() - start) * 1000

        if not results:
            print("No matching documents.")
        else:
            for doc in results:
                print(doc)
        print(f"({len(results)} matched, full scan in {elapsed_ms:.2f}ms)")

    def _cmd_stats(self):
        try:
            stats = self.db.cache.get_stats()
            print("WiredTiger session stats cursor acquired.")
            print(stats)
        except Exception as e:
            print(f"Could not fetch stats: {e}")


def main():
    db_name = sys.argv[1] if len(sys.argv) > 1 else "nebula_shell_db"
    NebulaShell(db_name=db_name).start()


if __name__ == "__main__":
    main()