import database as sqlite3

def test_db():
    try:
        user_id = '727718500663033897'
        db = sqlite3.connect("warnings.db")
        cursor = db.cursor()
        
        print("Inserting into reps...")
        cursor.execute("INSERT OR IGNORE INTO reps (user_id, rep_points) VALUES (?, 0)", (user_id,))
        
        print("Inserting into economy...")
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (user_id,))
        
        rep_amount = 1
        specie_reward = 5000
        
        print("Updating reps...")
        cursor.execute("UPDATE reps SET rep_points = rep_points + ? WHERE user_id = ?", (rep_amount, user_id))
        
        print("Updating economy...")
        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (specie_reward, user_id))
        
        print("Selecting reps...")
        cursor.execute("SELECT rep_points FROM reps WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        print("Row:", row)
        db.commit()
        db.close()
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

test_db()
