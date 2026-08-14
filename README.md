Below is a detailed `README.md` you can place at the root of your project.

```md
# NeBulaDB

NeBulaDB is a lightweight, file-backed document database with strict schema enforcement, JSON persistence, and a WiredTiger-based cache layer.

It provides a simple document-oriented API supporting collection creation, inserts, reads, updates, and deletes. Data is stored in a JSON file on disk, while read copies can be cached through WiredTiger for faster repeated access.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Schema Enforcement](#schema-enforcement)
- [Supported Field Types](#supported-field-types)
- [Python API Usage](#python-api-usage)
- [CLI Usage](#cli-usage)
- [Storage Format](#storage-format)
- [Caching Behavior](#caching-behavior)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Current Limitations](#current-limitations)
- [Troubleshooting](#troubleshooting)

---

## Overview

NeBulaDB is designed as a minimal embedded-style database engine. Each database instance is backed by a JSON file inside the `db/` directory. Collections are created with mandatory schemas, and every inserted or updated document is validated against that schema before being written.

The project also integrates a WiredTiger cache layer to cache frequently accessed documents. Reads first check the cache, and on a cache miss, the engine scans the in-memory collection, loads the document into the cache, and returns it.

---

## Features

- JSON file persistence
- Mandatory schema enforcement for every collection
- Field type validation
- Detection of missing fields
- Detection of unknown/extra fields
- Document insert, read, update, and delete operations
- Unique document ID enforcement inside each collection
- WiredTiger-based cache engine
- Cache-hit and cache-miss read flow
- Cache invalidation on update and delete
- Cache TTL support
- Simple CLI interface
- Integration tests for core database behavior and schema enforcement

---

## Architecture

NeBulaDB uses a write-through-style architecture:

1. Data is written to the in-memory collection structure.
2. The full database state is flushed to the JSON file on disk.
3. Cached read copies are invalidated on updates and deletes.
4. Reads check the WiredTiger cache first before scanning the primary collection.

High-level flow:

```text
           +-------------------+
           |   Application     |
           +---------+---------+
                     |
                     v
           +-------------------+
           |     NeBulaDB      |
           +---------+---------+
                     |
        +------------+------------+
        |                         |
        v                         v
+---------------+       +---------------------+
| JSON Storage  |       | WiredTiger Cache    |
| db/*.json     |       | db/*_cache          |
+---------------+       +---------------------+
```

### Read Flow

```text
Read Request
    |
    v
Check WiredTiger Cache
    |
    +--> Cache Hit --> Return cached document
    |
    +--> Cache Miss --> Scan in-memory collection
                         |
                         v
                      Store document in cache
                         |
                         v
                      Return document
```

### Write Flow

```text
Insert/Update Request
    |
    v
Validate schema
    |
    v
Modify in-memory collection
    |
    v
Flush JSON file
    |
    v
Invalidate cache entry
```

---

## Project Structure

```text
.
├── main.py              # Core database engine, schema validation, CLI
├── cache_engine.py      # WiredTiger cache wrapper
├── test.py              # Core integration tests
├── test_schema.py       # Schema enforcement tests
├── requirements.txt     # Python dependencies
└── db/                  # Runtime database and cache directory
```

The `db/` directory is created automatically when a database is initialized.

Example generated files:

```text
db/
├── mydb.json
└── mydb_cache/
```

---

## Requirements

Python dependencies:

```txt
wiredtiger==11.3.1
```

NeBulaDB uses the `wiredtiger` package for its cache engine.

---

## Installation

1. Clone or download the project.

2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate the virtual environment.

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Core Concepts

### Database

A database is represented by a JSON file under the `db/` directory.

Example:

```python
from main import NeBulaDB

db = NeBulaDB("mydb")
```

This creates or opens:

```text
db/mydb.json
```

and uses a WiredTiger cache directory:

```text
db/mydb_cache/
```

### Collection

A collection is a named list of documents.

Every collection must have a schema.

Example:

```python
schema = {
    "name": "string",
    "qty": "integer"
}

db.create_collection("products", schema)
```

### Document

A document is a dictionary stored inside a collection.

Each document has an `id` field assigned by the user.

Example:

```python
{
    "id": "item_01",
    "name": "laptop",
    "qty": 15
}
```

---

## Schema Enforcement

Schemas are mandatory for all collections.

When inserting or updating a document, NeBulaDB validates:

1. All required fields are present.
2. No unknown fields are present.
3. Each field matches its expected type.

### Example Valid Schema

```python
schema = {
    "name": "string",
    "rollno": "integer",
    "pass": "boolean",
    "marks": "float",
    "subjects": "array"
}
```

### Example Valid Document

```python
student = {
    "name": "John Doe",
    "rollno": 123,
    "pass": True,
    "marks": 89.5,
    "subjects": ["Math", "Science"]
}
```

### Validation Rules

| Rule | Behavior |
|---|---|
| Missing field | Insert/update is rejected |
| Extra field | Insert/update is rejected |
| Wrong type | Insert/update is rejected |
| Duplicate document ID | Insert is rejected |
| Non-existent collection | Operation is rejected |
| Missing schema | Operation is rejected |

---

## Supported Field Types

The `FieldType` class defines the supported schema types.

| FieldType Constant | String Value | Python Type Accepted |
|---|---|---|
| `FieldType.STRING` | `"string"` | `str` |
| `FieldType.INTEGER` | `"integer"` | `int`, excluding `bool` |
| `FieldType.FLOAT` | `"float"` | `int` or `float`, excluding `bool` |
| `FieldType.NUMBER` | `"number"` | `int` or `float`, excluding `bool` |
| `FieldType.BOOLEAN` | `"boolean"` | `bool` |
| `FieldType.ARRAY` | `"array"` | `list` |
| `FieldType.OBJECT` | `"object"` | `dict` |
| `FieldType.NULL` | `"null"` | `None` |

Important:

In Python, `True` and `False` are technically instances of `bool`, and `bool` is a subclass of `int`. NeBulaDB explicitly rejects booleans where integers, floats, or numbers are expected.

---

## Python API Usage

### Import the Database

```python
from main import NeBulaDB, FieldType
```

### Create a Database Instance

```python
db = NeBulaDB("mydb")
```

Optional cache limit parameter:

```python
db = NeBulaDB("mydb", max_cache=3)
```

Note: In the current WiredTiger-based cache implementation, cache sizing is handled through WiredTiger connection configuration.

---

### Create a Collection

```python
schema = {
    "name": "string",
    "qty": "integer"
}

result = db.create_collection("products", schema)
print(result)
```

Example output:

```text
Collection 'products' initialized with schema: {'name': 'string', 'qty': 'integer'}
```

---

### Insert a Document

```python
result = db.insert(
    "products",
    "item_01",
    {
        "name": "laptop",
        "qty": 15
    }
)

print(result)
```

Example output:

```text
Document item_01 committed to primary storage target.
```

---

### Read a Document

```python
result = db.read("products", "item_01")
print(result)
```

First read example:

```text
[Cache Miss -> Loaded] {'id': 'item_01', 'name': 'laptop', 'qty': 15}
```

Second read example:

```text
[Cache Hit] {'id': 'item_01', 'name': 'laptop', 'qty': 15}
```

---

### Update a Document

Updates require the full document payload because the entire document is validated against the schema.

```python
result = db.update(
    "products",
    "item_01",
    {
        "name": "gaming laptop",
        "qty": 10
    }
)

print(result)
```

Example output:

```text
Document item_01 mutated successfully.
```

---

### Delete a Document

```python
result = db.delete("products", "item_01")
print(result)
```

Example output:

```text
Document item_01 purged.
```

---

### Close the Database

```python
db.close()
```

This closes the underlying WiredTiger cache connection.

---

## CLI Usage

NeBulaDB includes a command-line interface.

```bash
python main.py <db_name> <collection> <action> [args...]
```

### Actions

| Action | Arguments | Description |
|---|---|---|
| `create` | `<schema_json>` | Create a collection with a schema |
| `insert` | `<id> <key:value...>` | Insert a document |
| `read` | `<id>` | Read a document |
| `update` | `<id> <key:value...>` | Update a document |
| `delete` | `<id>` | Delete a document |

---

### Create a Collection

```bash
python main.py shop products create '{"name": "string", "qty": "integer"}'
```

Example output:

```text
Collection 'products' initialized with schema: {'name': 'string', 'qty': 'integer'}
```

---

### Insert a Document

```bash
python main.py shop products insert item_01 name:laptop qty:15
```

Example output:

```text
Document item_01 committed to primary storage target.
```

The CLI attempts to parse each value as JSON first. If parsing fails, the value is stored as a string.

Examples:

```bash
qty:15
```

becomes:

```python
15
```

```bash
price:999.99
```

becomes:

```python
999.99
```

```bash
active:true
```

becomes:

```python
True
```

```bash
name:laptop
```

becomes:

```python
"laptop"
```

---

### Read a Document

```bash
python main.py shop products read item_01
```

Example first read:

```text
[Cache Miss -> Loaded] {'id': 'item_01', 'name': 'laptop', 'qty': 15}
```

Example second read:

```text
[Cache Hit] {'id': 'item_01', 'name': 'laptop', 'qty': 15}
```

---

### Update a Document

```bash
python main.py shop products update item_01 name:laptop qty:8
```

Example output:

```text
Document item_01 mutated successfully.
```

Important: because schema validation applies to the full document, updates should include all required fields.

---

### Delete a Document

```bash
python main.py shop products delete item_01
```

Example output:

```text
Document item_01 purged.
```

---

## Storage Format

Each database file stores both collections and schemas.

Example:

```json
{
    "collections": {
        "products": [
            {
                "id": "item_01",
                "name": "laptop",
                "qty": 15
            }
        ]
    },
    "schemas": {
        "products": {
            "name": "string",
            "qty": "integer"
        }
    }
}
```

The database file is flushed on every successful write operation.

---

## Caching Behavior

NeBulaDB uses WiredTiger as a cache layer through the `WiredTigerCache` class.

### Cache Location

For a database named `mydb`, cache files are stored under:

```text
db/mydb_cache/
```

### Cache Key Format

Documents are cached using the following key format:

```text
<collection>:<document_id>
```

Example:

```text
products:item_01
```

### TTL Entries

If a TTL is provided, an additional key is stored:

```text
<collection>:<document_id>__ttl
```

Example:

```text
products:item_01__ttl
```

The TTL value is stored as a Unix timestamp.

### Default Read TTL

When a document is loaded after a cache miss, it is cached with a TTL of 3600 seconds.

```python
self.cache.set(cache_key, doc, ttl_seconds=3600)
```

### Cache Invalidation

Cache entries are deleted when documents are updated or deleted.

This ensures that subsequent reads do not return stale cached documents.

---

## Testing

The project includes two test files.

### Run Core Integration Tests

```bash
python test.py
```

This tests:

- Database initialization
- Collection creation
- Insert operations
- Read operations
- Cache miss and cache hit behavior
- Cache persistence after restart
- Update operations
- Cache invalidation after update
- Delete operations

Expected final output:

```text
=== ALL ARCHITECTURAL TESTS PASSED SUCCESSFULLY ===
```

---

### Run Schema Enforcement Tests

```bash
python test_schema.py
```

This tests:

- Creating a collection with a schema
- Inserting valid documents
- Rejecting wrong field types
- Rejecting missing required fields
- Rejecting unknown/extra fields
- Updating documents with valid data
- Rejecting updates with invalid types
- Schema persistence across database restarts

Expected final output:

```text
=== ALL SCHEMA TESTS PASSED SUCCESSFULLY ===
```

---

## Error Handling

NeBulaDB returns error strings instead of raising unhandled exceptions during most user-facing operations.

### Common Error Messages

| Error | Meaning |
|---|---|
| `Error: Schema is mandatory for all collections.` | Collection creation requires a schema |
| `Error: Collection non-existent.` | The target collection does not exist |
| `Error: Collection schema missing (Strict Mode Enforced).` | The collection exists but has no schema |
| `Error: Duplicate ID.` | A document with the same ID already exists |
| `Error: Missing required field: <field>` | A required schema field was not provided |
| `Error: Unknown field: <field>` | The document contains a field not defined in the schema |
| `Error: Field '<field>' must be <type>` | The field value has the wrong type |
| `Error: Collection not found.` | The collection does not exist |
| `Error: Document context empty.` | The requested document was not found during read |
| `Error: Document target missing.` | The requested document was not found during update or delete |

---

## Current Limitations

- Updates require the full document payload.
- Partial updates are not supported.
- Documents are stored in memory as Python lists, so lookups by ID are O(N).
- There is no query engine or filtering system.
- There is no transaction support.
- There is no multi-user concurrency control.
- The CLI value parser is simple and relies on `key:value` formatting.
- Schema definitions are flat and do not currently validate nested object/array element types.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'wiredtiger'`

Install the dependency:

```bash
pip install -r requirements.txt
```

---

### WiredTiger installation issues

The `wiredtiger` package may require a compatible system environment and build tooling depending on your platform.

If installation fails, check:

- Python version compatibility
- System compiler availability
- WiredTiger availability for your operating system
- Virtual environment activation

---

### Stale cache or unexpected read results

Delete the database file and cache directory, then rerun.

For a database named `mydb`:

```bash
rm db/mydb.json
rm -rf db/mydb_cache
```

Windows PowerShell:

```powershell
Remove-Item db/mydb.json
Remove-Item db/mydb_cache -Recurse -Force
```

---

### Tests fail after manual changes

The test files clean up their own generated artifacts, but if a previous run was interrupted, manually remove the test database files.

For `test.py`:

```bash
rm db/test_warehouse.json
rm -rf db/test_warehouse_cache
```

For `test_schema.py`:

```bash
rm db/schema_test_db.json
rm -rf db/schema_test_db_cache
```
```