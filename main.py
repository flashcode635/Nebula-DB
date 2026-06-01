import sys  # Only for CLI arguments processing via sys.argv
from pathlib import Path

class NeBulaDB:
    def __init__(self, db_name, max_cache=3):
        self.max_cache = max_cache
        # Ensure `db/` directory exists and set db file path inside it
        self.db_dir = Path("db")
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / f"{db_name}.json"
        # Two-tier storage layout: Original structure + Read Copy (LRU Cache)
        self.collections = {}  # Original write-through target
        self.read_cache = {}   # Read Copy: { (coll, doc_id): doc_data }
        self._load_from_disk()

    def _load_from_disk(self):
        try:
            with open(self.db_path, "r") as f:
                content = f.read().strip()
                if content: self.collections = self._parse_json(content)
        except FileNotFoundError:
            self.collections = {}

    def _flush(self):
        # Writes directly to the original file target
        with open(self.db_path, "w") as f:
            f.write(self._serialize_json(self.collections))

    def _parse_json(self, s):
        # Minimalistic custom parser for string dictionary format
        s = s.strip()[1:-1].strip()
        if not s: return {}
        res, i = {}, 0
        while i < len(s):
            if s[i] == '"':
                start = i + 1
                end = s.find('"', start)
                key = s[start:end]
                i = s.find(':', end) + 1
                while s[i].isspace(): i += 1
                if s[i] == '[':
                    val_start = i
                    balance = 1
                    i += 1
                    while balance > 0:
                        if s[i] == '[': balance += 1
                        elif s[i] == ']': balance -= 1
                        i += 1
                    val_str = s[val_start:i]
                    res[key] = self._parse_list(val_str)
                i = s.find('"', i)
                if i == -1: break
        return res

    def _parse_list(self, s):
        s = s.strip()[1:-1].strip()
        if not s: return []
        res, i = [], 0
        while i < len(s):
            if s[i] == '{':
                start = i
                balance = 1
                i += 1
                while balance > 0:
                    if s[i] == '{': balance += 1
                    elif s[i] == '}': balance -= 1
                    i += 1
                obj_str = s[start:i]
                res.append(self._parse_obj(obj_str))
            i += 1
        return res

    def _parse_obj(self, s):
        s = s.strip()[1:-1].strip()
        if not s: return {}
        res = {}
        pairs = s.split(',')
        for p in pairs:
            if ':' not in p: continue
            k, v = p.split(':', 1)
            k = k.strip().strip('"')
            v = v.strip().strip('"')
            res[k] = v
        return res

    def _serialize_json(self, d):
        # Custom zero-dependency structural serializer
        parts = []
        for k, v in d.items():
            coll_parts = []
            for doc in v:
                doc_parts = [f'"{dk}":"{dv}"' for dk, dv in doc.items()]
                coll_parts.append("{" + ",".join(doc_parts) + "}")
            parts.append(f'"{k}":[' + ",".join(coll_parts) + "]")
        return "{" + ",".join(parts) + "}"

    def create_collection(self, coll_name):
        if coll_name not in self.collections:
            self.collections[coll_name] = []
            self._flush()
            return f"Collection '{coll_name}' initialized."
        return f"Collection '{coll_name}' already exists."

    def _update_lru(self, key, val):
        # Native Dict LRU implementation without collections library
        if key in self.read_cache:
            del self.read_cache[key]
        elif len(self.read_cache) >= self.max_cache:
            # Evict oldest entry (first item in iterator)
            oldest = next(iter(self.read_cache))
            del self.read_cache[oldest]
        self.read_cache[key] = val

    def insert(self, coll_name, doc_id, data_dict):
        if coll_name not in self.collections:
            return "Error: Collection non-existent."
        # Enforce unique identifiers within the collection array
        for doc in self.collections[coll_name]:
            if doc.get("id") == doc_id: return "Error: Duplicate ID."
        
        record = {"id": doc_id}
        record.update(data_dict)
        self.collections[coll_name].append(record)
        self._flush() # Standard Write-Through operation
        return f"Document {doc_id} committed to primary storage target."

    def read(self, coll_name, doc_id):
        # Access isolated Read Copy (LRU Cache Layer) first
        cache_key = (coll_name, doc_id)
        if cache_key in self.read_cache:
            self._update_lru(cache_key, self.read_cache[cache_key])
            return f"[Cache Hit] {self.read_cache[cache_key]}"
        
        # Read Miss -> Standard Linear O(N) Search on Original Object Array
        if coll_name not in self.collections: return "Error: Collection not found."
        for doc in self.collections[coll_name]:
            if doc.get("id") == doc_id:
                self._update_lru(cache_key, doc)  # Populate Read Copy Cache
                return f"[Cache Miss -> Loaded] {doc}"
        return "Error: Document context empty."

    def update(self, coll_name, doc_id, data_dict):
        if coll_name not in self.collections: return "Error: Collection not found."
        for doc in self.collections[coll_name]:
            if doc.get("id") == doc_id:
                doc.update(data_dict)
                self._flush()
                # Invalidate existing isolated read copies to enforce consistency
                cache_key = (coll_name, doc_id)
                if cache_key in self.read_cache: del self.read_cache[cache_key]
                return f"Document {doc_id} mutated successfully."
        return "Error: Document target missing."

    def delete(self, coll_name, doc_id):
        if coll_name not in self.collections: return "Error: Collection not found."
        initial_len = len(self.collections[coll_name])
        self.collections[coll_name] = [d for d in self.collections[coll_name] if d.get("id") != doc_id]
        if len(self.collections[coll_name]) < initial_len:
            self._flush()
            cache_key = (coll_name, doc_id)
            if cache_key in self.read_cache: del self.read_cache[cache_key]
            return f"Document {doc_id} purged."
        return "Error: Document target missing."

# --- CLI Execution Layer ---
if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 3:
        print("Usage: python nosql_db.py <db_name> <collection> <action> [args...]")
        print("Actions: create, insert <id> <k:v...>, read <id>, update <id> <k:v...>, delete <id>")
        sys.exit(1)

    db = NeBulaDB(args[0])
    coll, action = args[1], args[2]

    if action == "create":
        print(db.create_collection(coll))
    elif action in ("insert", "update") and len(args) >= 5:
        payload = {}
        for item in args[4:]:
            if ":" in item:
                k, v = item.split(":", 1)
                payload[k] = v
        method = getattr(db, action)
        print(method(coll, args[3], payload))
    elif action in ("read", "delete") and len(args) == 4:
        method = getattr(db, action)
        print(method(coll, args[3]))
    else:
        print("Invalid Argument Configuration matrix structural limit reached.")
