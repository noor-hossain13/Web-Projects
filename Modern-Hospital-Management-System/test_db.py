import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',  # Empty for XAMPP default
        database='hospital_db'
    )
    print("✅ MySQL Connection Successful!")
    print(f"Database: {connection.db.decode()}")
    connection.close()
except Exception as e:
    print(f"❌ Connection Failed: {e}")