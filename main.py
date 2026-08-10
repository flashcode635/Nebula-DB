import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class FieldType:
    """Supported data types in application"""
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    INTEGER = 'integer'
    FLOAT = 'float'
    ARRAY = 'array'
    OBJECT = 'object'
    NULL = 'null'

class Schema:
    def __init__(self, fields: Dict[str, str]):
        """Define schema for a collection"""
        self.fields = fields
        
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate if data matches the schema"""
        # Check all required fields exist
        for field, field_type in self.fields.items():
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            
            value = data[field]
            
            # Type validation
            if field_type == FieldType.STRING:
                if not isinstance(value, str):
                    raise TypeError(f"Field '{field}' must be string, got {type(value).__name__}")
            elif field_type == FieldType.INTEGER:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise TypeError(f"Field '{field}' must be integer, got {type(value).__name__}")
            elif field_type == FieldType.FLOAT:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise TypeError(f"Field '{field}' must be float, got {type(value).__name__}")
            elif field_type == FieldType.NUMBER:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise TypeError(f"Field '{field}' must be number, got {type(value).__name__}")
            elif field_type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    raise TypeError(f"Field '{field}' must be boolean, got {type(value).__name__}")
            elif field_type == FieldType.ARRAY:
                if not isinstance(value, list):
                    raise TypeError(f"Field '{field}' must be array, got {type(value).__name__}")
            elif field_type == FieldType.OBJECT:
                if not isinstance(value, dict):
                    raise TypeError(f"Field '{field}' must be object, got {type(value).__name__}")
            elif field_type == FieldType.NULL:
                if value is not None:
                    raise TypeError(f"Field '{field}' must be null, got {type(value).__name__}")
        
        # Check for extra fields
        for field in data.keys():
            if field not in self.fields:
                raise ValueError(f"Unknown field: {field}")
                
        return True

class NeBulaDB:
    def __init__(self, db_name, max_cache=3):
        self.max_cache = max_cache
        self.db_dir = Path("db")
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / f"{db_name}.json"
        self.collections = {}  
        self.schemas = {}  # Store schema definitions
        self.read_cache = {}   
        self._load_from_disk()

    def _load_from_disk(self):
        try:
            with open(self.db_path, "r") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    self.collections = data.get("collections", {})
                    schema_defs = data.get("schemas", {})
                    self.schemas = {name: Schema(fields) for name, fields in schema_defs.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            self.collections = {}
            self.schemas = {}

    def _flush(self):
        data = {
            "collections": self.collections,
            "schemas": {name: schema.fields for name, schema in self.schemas.items()}
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def create_collection(self, coll_name, schema=None):
        if coll_name not in self.collections:
            self.collections[coll_name] = []
            if schema:
                self.schemas[coll_name] = Schema(schema)
            self._flush()
            msg = f"Collection '{coll_name}' initialized."
            if schema: msg += f" with schema: {schema}"
            return msg
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
        
        # Validate against schema if it exists
        if coll_name in self.schemas:
            try:
                self.schemas[coll_name].validate(data_dict)
            except (ValueError, TypeError) as e:
                return f"Error: {e}"

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
        
        # Validate against schema if it exists
        if coll_name in self.schemas:
            try:
                self.schemas[coll_name].validate(data_dict)
            except (ValueError, TypeError) as e:
                return f"Error: {e}"

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
        print("Usage: python main.py <db_name> <collection> <action> [args...]")
        print("Actions: create [schema_json], insert <id> <k:v...>, read <id>, update <id> <k:v...>, delete <id>")
        sys.exit(1)

    db = NeBulaDB(args[0])
    coll, action = args[1], args[2]

    if action == "create":
        schema = None
        if len(args) >= 4:
            try:
                schema = json.loads(args[3])
            except json.JSONDecodeError:
                print("Error: Invalid schema JSON.")
                sys.exit(1)
        print(db.create_collection(coll, schema))
    elif action in ("insert", "update") and len(args) >= 5:
        payload = {}
        for item in args[4:]:
            if ":" in item:
                k, v = item.split(":", 1)
                try:
                    # Attempt to parse as JSON to support int, bool, etc.
                    v = json.loads(v)
                except json.JSONDecodeError:
                    # Fallback to string if not valid JSON
                    pass
                payload[k] = v
        method = getattr(db, action)
        print(method(coll, args[3], payload))
    elif action in ("read", "delete") and len(args) == 4:
        method = getattr(db, action)
        print(method(coll, args[3]))
    else:
        print("Invalid Argument Configuration matrix structural limit reached.")

