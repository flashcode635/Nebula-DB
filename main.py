import json
import uuid
from pathlib import Path

# insert in db
def insert_db (data, filename="game_save.json", folder="db"):

    # Create folder if it doesn't exist
    Path(folder).mkdir(parents=True, exist_ok=True)
    data["id"]= str(uuid.uuid4())
   
    filepath = Path(folder) / filename
    with open(filepath, 'a') as f:
        json.dump(data, f, indent=4)

# fetch it back
def read_db(filename, folder="db"):
    """Load a dictionary from a JSON file."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    
    filepath = Path(folder) / filename
    with open(filepath, 'r') as f:
        return json.load(f)
    
data = {
    "name": "Alice",
    "age": 30,
    "hobbies": ["reading", "hiking"],
    }

insert_db (data, "user1.json")  
res= read_db("user1.json")
print(res)
print(type(res)) 