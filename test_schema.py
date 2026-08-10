import os
import json
from main import NeBulaDB, FieldType

def test_schema_enforcement():
    db_name = "schema_test_db"
    json_file = f"db/{db_name}.json"
    if os.path.exists(json_file):
        os.remove(json_file)

    db = NeBulaDB(db_name)

    # 1. Create collection with schema
    schema_def = {
        'name': FieldType.STRING,
        'rollno': FieldType.INTEGER,
        'pass': FieldType.BOOLEAN,
        'marks': FieldType.FLOAT,
        'subjects': FieldType.ARRAY
    }
    print(db.create_collection('students', schema_def))

    # 2. Insert valid data
    student1 = {
        'name': 'John Doe',
        'rollno': 123,
        'pass': True,
        'marks': 89.5,
        'subjects': ['Math', 'Science']
    }
    res = db.insert('students', 's1', student1)
    print(res)
    assert "committed" in res

    # 3. Try inserting invalid data (wrong type)
    invalid_student = {
        'name': 'Jane Doe',
        'rollno': '123',  # Should be integer
        'pass': True,
        'marks': 90.0,
        'subjects': []
    }
    res = db.insert('students', 's2', invalid_student)
    print(f"Invalid insert (wrong type) result: {res}")
    assert "Error" in res and "must be integer" in res

    # 4. Try inserting invalid data (missing field)
    missing_field_student = {
        'name': 'Jane Doe',
        'rollno': 456,
        'pass': True
        # marks and subjects missing
    }
    res = db.insert('students', 's3', missing_field_student)
    print(f"Invalid insert (missing field) result: {res}")
    assert "Error" in res and "Missing required field" in res

    # 5. Try inserting invalid data (extra field)
    extra_field_student = {
        'name': 'Jane Doe',
        'rollno': 456,
        'pass': True,
        'marks': 90.0,
        'subjects': [],
        'age': 20
    }
    res = db.insert('students', 's4', extra_field_student)
    print(f"Invalid insert (extra field) result: {res}")
    assert "Error" in res and "Unknown field" in res

    # 6. Test update with valid data
    update_data = student1.copy()
    update_data['marks'] = 95.0
    res = db.update('students', 's1', update_data)
    print(f"Valid update result: {res}")
    assert "mutated successfully" in res

    # 7. Test update with invalid data
    invalid_update = student1.copy()
    invalid_update['pass'] = 'not-a-bool'
    res = db.update('students', 's1', invalid_update)
    print(f"Invalid update result: {res}")
    assert "Error" in res and "must be boolean" in res

    # 8. Test persistence
    db.close() # Actually NeBulaDB doesn't have close, but it flushes on every write
    
    db2 = NeBulaDB(db_name)
    assert 'students' in db2.schemas
    assert db2.schemas['students'].fields['rollno'] == FieldType.INTEGER
    print("Persistence test passed.")

    print("\n=== ALL SCHEMA TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    # Add a dummy close method to NeBulaDB if it doesn't exist to match the example usage
    if not hasattr(NeBulaDB, 'close'):
        NeBulaDB.close = lambda self: None
        
    test_schema_enforcement()
