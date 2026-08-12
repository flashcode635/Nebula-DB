import os
import shutil
from main import NeBulaDB

def run_tests():
    db_name = "test_warehouse"
    db_dir = "db"
    json_file = os.path.join(db_dir, f"{db_name}.json")
    cache_dir = os.path.join(db_dir, f"{db_name}_cache")
    
    # Reset any existing test artifacts to ensure a clean environment state
    if os.path.exists(json_file):
        os.remove(json_file)
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        
    print("=== STARTING ARCHITECTURAL INTEGRATION TESTS ===")

    # 1. Instantiate DB Engine
    db = NeBulaDB(db_name)

    # 2. Test Collection Creation
    print("\n[TEST 1] Initializing structural collection layers...")
    print(db.create_collection("my-shop", {"name": "string", "qty": "string"}))

    # 3. Test Write Operations (Write-Through Architecture)
    print("\n[TEST 2] Executing write-through operations...")
    print(db.insert("my-shop", "item_01", {"name": "laptop", "qty": "15"}))
    print(db.insert("my-shop", "item_02", {"name": "phone", "qty": "30"}))
    print(db.insert("my-shop", "item_03", {"name": "tablet", "qty": "45"}))
    # Verify that data exists inside the original memory structure
    assert len(db.collections["my-shop"]) == 3, "Failed: Write-through matrix mismatch."

    # 4. Test Read Copies and Caching Flow
    print("\n[TEST 3] Verifying Cache Isolation and Miss -> Hit flow...")
    # First access: Must result in a cache miss (scans original data array)
    res1 = db.read("my-shop", "item_01")
    print(res1)
    assert "[Cache Miss -> Loaded]" in res1, "Failed: Expected Cache Miss on initial data read."
    # Immediate secondary access: Must resolve from the isolated Read Copy cache
    res2 = db.read("my-shop", "item_01")
    print(res2)
    assert "[Cache Hit]" in res2, "Failed: Expected Cache Hit on sequential data read."

    # 5. Skip manual LRU eviction test as WiredTiger uses memory-based eviction
    print("\n[TEST 4] WiredTiger Cache persistence verification...")
    # item_01 is already in cache.
    # We will close the DB and reopen it, then check if it's still a Cache Hit.
    db.close()
    
    db = NeBulaDB(db_name)
    res_persistent = db.read("my-shop", "item_01")
    print(f"Re-access after restart: {res_persistent}")
    assert "[Cache Hit]" in res_persistent, "Failed: Cache did not persist after restart."

    # 6. Test Data Mutation (Update Engine & Cache Invalidation)
    print("\n[TEST 5] Testing record mutations and cache coherency updates...")
    # Mutate item_02
    print(db.update("my-shop", "item_02", {"name": "phone", "qty": "28"}))
    
    # Verify reading item_02 fetches fresh data through a cache miss (invalidation worked)
    res4 = db.read("my-shop", "item_02")
    print(res4)
    assert "[Cache Miss -> Loaded]" in res4 and "28" in res4, "Failed: Cache stale after update."

    # 7. Test Data Erasure and Purging Mechanics
    print("\n[TEST 6] Testing record deletion operations...")
    print(db.delete("my-shop", "item_03"))

    # Verify record is entirely absent from the storage structures
    assert len(db.collections["my-shop"]) == 2, "Failed: Item was not purged from original database."
    res_deleted = db.read("my-shop", "item_03")
    print(res_deleted)
    assert "Error" in res_deleted, "Failed: Item still readable after deletion."
    
    db.close()
    
    # Clean up file artifact after completing verification
    if os.path.exists(json_file):
        os.remove(json_file)
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        
    print("\n=== ALL ARCHITECTURAL TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_tests()