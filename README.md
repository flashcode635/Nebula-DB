# NebulaDB

An embedded, schema-driven database engine with WiredTiger-backed caching and an interactive REPL shell. NebulaDB provides type-safe collection management with full CRUD operations, schema validation, and TTL-enabled caching.

## Features

- **Schema-Based Collections**: Define strict schemas for your collections with type validation
- **Type Safety**: Supports multiple field types (String, Integer, Float, Number, Boolean, Array, Object, Null)
- **CRUD Operations**: Full support for Create, Read, Update, and Delete operations
- **WiredTiger Caching**: High-performance caching layer with configurable size and TTL support
- **Write-Through Strategy**: Automatic cache invalidation on updates for data consistency
- **Interactive REPL Shell**: User-friendly command-line interface for database operations
- **Persistent Storage**: Data is stored in JSON format on disk
- **Efficient Querying**: Filter data using common comparison operators (=, !=, >, <, >=, <=)

## Project Structure

```
NebulaDB/
├── main.py                # Core database engine (NeBulaDB class)
├── cache_engine.py        # WiredTiger caching implementation
├── shell.py               # Interactive REPL shell
├── test_schema.py         # Schema validation tests
├── test.py                # Additional tests
├── requirements.txt       # Project dependencies
├── post.txt               # Post-implementation notes
└── db/                    # Data directory (created at runtime)
    ├── nebula_shell_db.json       # Persisted data
    └── nebula_shell_db_cache/     # WiredTiger cache files
```

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository_url>
cd NebulaDB
```

### 2. Create a Virtual Environment

Linux/macOS:

```bash
python3 -m venv .venv
```

Windows:

```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Shell Mode (Recommended)

Start the interactive REPL shell:

```bash
python shell.py
```

Or specify a custom database name:

```bash
python shell.py my_custom_db
```

#### Shell Commands

**Create a Collection with Schema**

```bash
CREATE COLLECTION users {"name":"string","age":"integer","email":"string","active":"boolean"}
```

**Insert a Document**

```bash
INSERT INTO users u1 {"name":"Ramit","age":22,"email":"ramit@example.com","active":true}
```

**Read a Document**

```bash
READ users u1
```

**Update a Document**

```bash
UPDATE users u1 {"age":23}
```

**Delete a Document**

```bash
DELETE users u1
```

**Query with Filters**

```bash
FIND IN users WHERE age > 20
```

Supported operators: `=`, `!=`, `>`, `<`, `>=`, `<=`

**View Cache Statistics**

```bash
STATS
```

**Display Help**

```bash
HELP
```

**Exit the Shell**

```bash
EXIT
```

or

```bash
QUIT
```

### Programmatic Usage

Use NebulaDB directly in Python code:

```python
from main import NeBulaDB, FieldType

# Initialize database
db = NeBulaDB("my_app_db")

# Create a collection with schema
schema = {
    'name': FieldType.STRING,
    'age': FieldType.INTEGER,
    'email': FieldType.STRING,
    'active': FieldType.BOOLEAN
}
print(db.create_collection('users', schema))

# Insert a document
user_data = {
    'name': 'John Doe',
    'age': 30,
    'email': 'john@example.com',
    'active': True
}
print(db.insert('users', 'user_1', user_data))

# Read a document
print(db.read('users', 'user_1'))

# Update a document
print(db.update('users', 'user_1', {'age': 31}))

# Delete a document
print(db.delete('users', 'user_1'))

# Close connection
db.close()
```

## Supported Field Types

The `FieldType` class defines all supported data types:

| Type      | Description       | Example            |
| --------- | ----------------- | ------------------ |
| `STRING`  | Text data         | `"John"`           |
| `INTEGER` | Whole numbers     | `42`               |
| `FLOAT`   | Decimal numbers   | `3.14`             |
| `NUMBER`  | Integer or float  | `42` or `3.14`     |
| `BOOLEAN` | True/False values | `true`             |
| `ARRAY`   | List of items     | `[1, 2, 3]`        |
| `OBJECT`  | Nested object     | `{"key": "value"}` |
| `NULL`    | Null value        | `null`             |

## Caching System

NebulaDB uses WiredTiger for efficient caching:

- **Cache Size**: Configurable per database instance (default: 100MB)
- **TTL Support**: Set expiration time for cached entries (optional)
- **Automatic Invalidation**: Cache is cleared on document updates/deletes
- **Cache Hits**: First read returns cached value if available
- **Cache Misses**: Data is fetched from disk and cached for future reads

Example with TTL:

```python
# Documents cached for 1 hour (3600 seconds)
db.read('users', 'user_1')
```

## Testing

Run the schema validation tests:

```bash
python test_schema.py
```

Run additional tests:

```bash
python test.py
```

## Implementation Notes

### Day-2 Improvement: Persistent Shell Connection

The `shell.py` implements a critical improvement from Day-2 notes:

- **Before**: Each command spawned a new Python process, tearing down the WiredTiger cache
- **After**: Single persistent connection maintains cache across all commands

This significantly improves performance for interactive workflows.

### Data Persistence

- Collections are stored as JSON in `db/{db_name}.json`
- Schema definitions are preserved with collection data
- WiredTiger cache files are stored in `db/{db_name}_cache/`

### Error Handling

The system enforces strict schema validation:

- Required fields must be present
- Field values must match declared types
- Duplicate document IDs are rejected
- Unknown fields are rejected

## Dependencies

- **wiredtiger** (11.3.1): High-performance storage engine for caching

## Troubleshooting

### Virtual Environment Issues

If commands are not found after activation, try:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell requires execution policy adjustment)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\activate
```

### WiredTiger Connection Errors

Ensure the `db/` directory exists and is writable:

```bash
mkdir -p db
```

### Cache Issues

Clear the cache directory to reset:

```bash
rm -rf db/nebula_shell_db_cache/
```

## Support & Contribution

For issues, suggestions, or contributions, please review the project code and open discussions as needed.

---

**Version**: 0.1  
**Database Engine**: WiredTiger 11.3.1  
**Python Version**: 3.7+
