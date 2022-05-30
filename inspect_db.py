import sqlite3

# local db file directory
DB_FILE = 'data/hx_analyst_exercise.db'  

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# list all tables [making sure its same as csv's]
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables found:", [t[0] for t in tables])
print()

# inspecting each table
for (table_name,) in tables:
    print(f"== Table: {table_name} ==")

    # showing col names
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    print("Columns:", col_names)

    # previewing first 5 rows
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;") # data same as csv's from preview
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    print()

conn.close()
