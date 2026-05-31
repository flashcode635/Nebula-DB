import os
from main import DataBase  # Import your class from the other file

TEST_DB = "test_db.json"

"""remove the testing db if exist earlier"""
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
def run_tests():
    clean_db() # Start fresh
    db = DataBase(TEST_DB)

    # 1. Test Create & Read
    db.create("contacts", "c1", {"name": "Xavier", "email": "x@test.com"})
    assert db.read("contacts", "c1")["name"] == "Xavier", "Create/Read failed"

    # 2. Test Update
    db.update("contacts", "c1", {"phone": "123"})
    assert db.read("contacts", "c1")["phone"] == "123", "Update failed"

    # 3. Test Search (Partial)
    db.create("contacts", "c2", {"name": "Alice", "email": "a@gmail.com"})
    results = db.search("contacts", "email", "@gmail.com", partial=True)
    assert len(results) == 1 and results[0]["name"] == "Alice", "Search failed"

    # 4. Test Domain Logic (Inventory)
    db.create("inventory", "i1", {"name": "Laptop", "quantity": 5})
    db.adjust_inventory("i1", -2)
    assert db.read("inventory", "i1")["quantity"] == 3, "Inventory adjust failed"

    # 5. Test Key-Value Store
    db.kv_set("theme", "dark")
    assert db.kv_get("theme") == "dark", "KV store failed"

    # 6. Test Delete
    db.delete("contacts", "c1")
    assert db.read("contacts", "c1") is None, "Delete failed"

    clean_db() # Cleanup
    print("✅ All tests passed!")

if __name__ == "__main__":
    run_tests()