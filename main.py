import json
from pathlib import Path

class DataBase:
    def __init__(self, filepath="db/db.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        if self.filepath.exists():
            return json.loads(self.filepath.read_text())
        return {"contacts": {}, "inventory": {}, "records": {}, "keyvalue": {}}

    def _save(self):
        self.filepath.write_text(json.dumps(self.data, indent=2))

    # --- Core CRUD (O(1) Speed) ---
    def create(self, collection, record_id, data):
        if collection not in self.data: self.data[collection] = {}
        self.data[collection][str(record_id)] = data
        self._save()

    def read(self, collection, record_id):
        return self.data.get(collection, {}).get(str(record_id))

    def update(self, collection, record_id, data):
        if str(record_id) in self.data.get(collection, {}):
            self.data[collection][str(record_id)].update(data)
            self._save()

    def delete(self, collection, record_id):
        if self.data.get(collection, {}).pop(str(record_id), None) is not None:
            self._save()

    # --- Querying & Search (O(n) Speed) ---
    def search(self, collection, field=None, value=None, partial=False):
        records = self.data.get(collection, {}).values()
        if not field: return list(records)
        if partial: return [r for r in records if value in str(r.get(field, ""))]
        return [r for r in records if r.get(field) == value]

    # --- Domain Specific Features ---
    def adjust_inventory(self, item_id, amount):
        item = self.data["inventory"].get(str(item_id))
        if item and "quantity" in item:
            item["quantity"] = max(0, item["quantity"] + amount)
            self._save()
            return item["quantity"]
        return None

    def kv_set(self, key, value):
        self.data["keyvalue"][key] = value
        self._save()

    def kv_get(self, key):
        return self.data["keyvalue"].get(key)
    

    # testing
