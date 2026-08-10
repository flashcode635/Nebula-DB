import os
from main import NeBulaDB

def run_tests():
    db_name = "test_warehouse"
    json_file = f"{db_name}.json"
    # Reset any existing test artifacts to ensure clean environment state
    if os.path.exists(json_file):
        os.remove(json_file)
    print("=== STARTING ARCHITECTURAL INTEGRATION TESTS ===")

    # 1. Instantiate DB Engine with an isolated 2-slot maximum Read Cache
    db = NeBulaDB(db_name, max_cache=2)

    # 2. Test Collection Creation
    print("\n[TEST 1] Initializing structural collection layers...")
    print(db.create_collection("my-shop"))

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

    # 5. Test Manual LRU Eviction Boundary Metrics
    print("\n[TEST 4] Testing custom LRU eviction behavior (Cache Cap = 2)...")

    # Populate cache slot 2 with item_02
    print(db.read("my-shop", "item_02"))  # Cache contains: item_01 (oldest), item_02 (newest)

    # Access item_03: This must force eviction of the oldest element (item_01)
    print(db.read("my-shop", "item_03"))  # Cache contains: item_02, item_03. item_01 evicted.

    # Re-access item_01: Must trigger a Cache Miss because it was pushed out of memory boundary
    res3 = db.read("my-shop", "item_01")
    print(res3)
    assert "[Cache Miss -> Loaded]" in res3, "Failed: LRU eviction failed to dump oldest entry."

    # 6. Test Data Mutation (Update Engine & Cache Invalidation)
    print("\n[TEST 5] Testing record mutations and cache coherency updates...")
    # Cache item_02
    db.read("my-shop", "item_02")
    # Mutate item_02: Should wipe out its corresponding read copy to prevent dirty reads

    print(db.update("my-shop", "item_02", {"qty": "28"}))
    # Verify modification reflects inside original collection array
    for doc in db.collections["my-shop"]:
        if doc["id"] == "item_02":
            assert doc["qty"] == "28", "Failed: Mutated state not updated in memory."

    # Verify reading item_02 fetches fresh data through a cache miss
    res4 = db.read("my-shop", "item_02")
    print(res4)
    assert "[Cache Miss -> Loaded]" in res4 and "28" in res4, "Failed: Cache stale after update."

    # 7. Test Data Erasure and Purging Mechanics
    print("\n[TEST 6] Testing record deletion operations...")
    print(db.delete("my-shop", "item_03"))

    # Verify record is entirely absent from the storage structures
    assert len(db.collections["my-shop"]) == 2, "Failed: Item was not purged from original database."
    print(db.read("my-shop", "item_03"))  # Should output standard error text
    
    # Clean up file artifact after completing verification
    if os.path.exists(json_file):
        os.remove(json_file)
    print("\n=== ALL ARCHITECTURAL TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_tests()