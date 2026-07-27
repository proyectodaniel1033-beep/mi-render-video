import json

DB_FILE = "/tmp/jobs.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

# Y reemplaza las operaciones sobre 'jobs_db[job_id]' por:
# db = load_db()
# db[job_id] = ...
# save_db(db)
