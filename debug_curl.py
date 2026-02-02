from utils.database import DatabaseHandler

with DatabaseHandler() as db:
    # Get full row for Dumbbell Curl
    results = db.fetch_all(
        "SELECT * FROM workout_log WHERE exercise = 'Dumbbell Curl' ORDER BY created_at DESC LIMIT 3"
    )
    print("Dumbbell Curl workout data:")
    for r in results:
        print(f"  Row: {dict(r)}")
    
    # Check table schema
    print("\nColumn names in workout_log:")
    schema = db.fetch_all("PRAGMA table_info(workout_log)")
    for col in schema:
        print(f"  - {col['name']} ({col['type']})")
