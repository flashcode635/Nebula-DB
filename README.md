# NeBula DB

A minimal, zero-dependency, write-through NoSQL Document Database engine built entirely from scratch in pure Python. **NeBula DB** operates without a single external library import and implements an isolated, two-tier storage layer consisting of a primary flat-file data array and an independent LRU (Least Recently Used) read cache.

---

## Architecture Design Matrix

```
   [ CLI Client Interface ]
              |
              v
     [ NoSQLDB Engine Core ]
      /                 \
     / (Read Miss)       \ (Write / Mutate / Delete)
    v                     v
[LRU Read Cache]   [Primary In-Memory Cache]
(Read Copy Layer)         |
                          v
               [Custom Serialization Layer]
                          |
                          v
               [Flat File Storage Layer] (.json)

```

### Architectural Features

* **Zero Dependencies (D1 Compilers-Ready):** No `json`, `csv`, or `collections` standard library modules are imported. All structural lexical analysis and object serializations are processed manually.
* **Line Budget Optimized (D2 Compliant):** Full operational engine implementation fits cleanly under the strict 200-line operational constraint budget.
* **Dual-Tier Memory Topology:** Writes flow safely into a permanent storage layout, while frequent reads are mapped into an active read copy cache optimized with an exact insertion-order LRU eviction routine.

---

## Installation & Setup

Clone or place `main.py` in your development pipeline.

```bash
# Ensure executable file availability in your workspace
python main.py

```

---

## CLI Production Matrix Execution

Interact with the engine through the terminal using standard argument vector structures:

### 1. Initialize a Structural Database and Collection

Creates an isolated datastore mapping to a raw target structure file on the disk.

```bash
python main.py cluster0 users create

```

### 2. Insert Structured Document Fields

Commits flat entries directly down into the database layer via automated write-through execution.

```bash
python main.py cluster0 users insert u1 name:Alice role:Admin dept:Security
python main.py cluster0 users insert u2 name:Bob role:Developer dept:Eng

```

### 3. Read Operations (Dual-Tier Pipeline Processing)

* **First Read Execution ($O(N)$ Scan):** Scans the primary data array for a key match, extracts the entity fields, updates the cache, and outputs a `Cache Miss`.

```bash
python main.py cluster0 users read u1
# Output: [Cache Miss -> Loaded] {'id': 'u1', 'name': 'Alice', 'role': 'Admin', 'dept': 'Security'}

```

* **Consecutive Read Execution ($O(1)$ Lookups):** Fetches properties instantly from the high-performance read-copy space directly.

```bash
python main.py cluster0 users read u1
# Output: [Cache Hit] {'id': 'u1', 'name': 'Alice', 'role': 'Admin', 'dept': 'Security'}

```

### 4. Mutate Data Fields (Update Logic)

Mutates attributes on structural nodes and actively purges the target's associated cache slot to force system-wide data coherence.

```bash
python main.py cluster0 users update u1 role:SuperAdmin

```

### 5. Purge Records (Delete Operation)

Erases document traces from file layouts and memory boundaries permanently.

```bash
python main.py cluster0 users delete u2

```

---

## Core Specification Engine Testing

An automated test program (`test.py`) is bundled alongside the codebase to programmatically guarantee engine operations across memory allocation, cache eviction rules, and file updates.

```bash
python test.py

```