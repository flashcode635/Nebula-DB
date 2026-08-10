<<<<<<< HEAD
# NeBula DB

A minimal, zero-dependency, write-through NoSQL Document Database engine built entirely from scratch in pure Python. **NeBula DB** provides a schema-validated storage layer with an independent LRU (Least Recently Used) read cache, ensuring type safety and high-performance lookups.

---

## Architecture Design Matrix

```
   [ CLI Client Interface ]
              |
              v
     [ NoSQLDB Engine Core ]
              |
      [ Schema Validator ]  <-- (Type Enforcement Layer)
      /                 \
     / (Read Miss)       \ (Write / Mutate / Delete)
    v                     v
[LRU Read Cache]   [Primary In-Memory Cache]
(Read Copy Layer)         |
                          v
               [Standard JSON Storage Layer]
                          |
                          v
               [Flat File Storage Layer] (.json)

```

### Architectural Features

* **No External Dependencies:** Zero third-party packages required. Uses Python's standard `json` and `pathlib` modules for robust data serialization and cross-platform path handling.
* **Schema Enforcement:** Supports optional collection-level schemas to enforce data types (int, float, bool, etc.) and required fields at the engine level.
* **Dual-Tier Memory Topology:** Writes flow safely into a permanent storage layout, while frequent reads are mapped into an active read copy cache optimized with an exact insertion-order LRU eviction routine.
* **Line Budget Optimized:** Core logic remains compact and efficient, maintaining high performance under minimal resource constraints.

---

## Installation & Setup

Clone or place `main.py` in your development pipeline.

```bash
# Ensure executable file availability in your workspace
python main.py

```

---

## CLI Production Matrix Execution

Interact with the engine through the terminal. The CLI supports typed data parsing and schema definitions.

### 1. Initialize a Collection (with Optional Schema)

Creates a collection. You can pass a JSON schema to enforce types.

**Without Schema:**
```bash
python main.py cluster0 users create
```

**With Schema:**
```bash
python main.py cluster0 students create '{"name": "string", "rollno": "integer", "pass": "boolean"}'
```
*Supported Types:* `string`, `integer`, `float`, `number`, `boolean`, `array`, `object`, `null`.

### 2. Insert Typed Documents

The CLI automatically parses values as JSON to support types. Strings that aren't valid JSON (like plain names) are treated as standard strings.

```bash
# Alice is string, 123 is integer, true is boolean
python main.py cluster0 students insert s1 name:Alice rollno:123 pass:true
```

### 3. Read Operations (Dual-Tier Pipeline Processing)

* **First Read Execution ($O(N)$ Scan):** Scans the primary data array, updates the cache, and outputs a `Cache Miss`.

```bash
python main.py cluster0 students read s1
# Output: [Cache Miss -> Loaded] {'id': 's1', 'name': 'Alice', 'rollno': 123, 'pass': True}

```

* **Consecutive Read Execution ($O(1)$ Lookups):** Fetches properties instantly from the LRU cache.

```bash
python main.py cluster0 students read s1
# Output: [Cache Hit] {'id': 's1', 'name': 'Alice', 'rollno': 123, 'pass': True}

```

### 4. Schema Validation Errors

If you attempt to insert data that violates the schema, the engine will block the write:

```bash
python main.py cluster0 students insert s2 name:Bob rollno:twenty
# Output: Error: Field 'rollno' must be integer, got str
```

### 5. Mutate & Delete Data

```bash
# Update
python main.py cluster0 students update s1 rollno:124

# Delete
python main.py cluster0 students delete s1
```

---

## Core Specification Engine Testing

The database includes automated tests for both architectural integrity and schema enforcement.

```bash
# Test core architecture (Cache, CRUD, Persistence)
python test.py

# Test schema validation (Types, Required fields, Extra fields)
python test_schema.py

=======
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

>>>>>>> b1ba09dac53d0ff8222dfa9871382a7cbe03f401
```