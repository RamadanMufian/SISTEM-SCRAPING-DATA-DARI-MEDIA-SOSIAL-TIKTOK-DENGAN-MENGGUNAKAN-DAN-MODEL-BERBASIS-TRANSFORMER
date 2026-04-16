# initialize_app.py
import pymysql
from database import engine, DB_NAME, DB_CONFIGS
from models_db import Base

def create_database():
    """Create the database if it doesn't exist"""
    print(f"🔍 Checking/Creating database: {DB_NAME}...")
    
    success = False
    for config in DB_CONFIGS:
        try:
            # Connect without database specified
            conn = pymysql.connect(
                host=config['host'],
                user=config['user'],
                password=config['password'],
                port=config['port']
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.close()
            print(f"✅ Database {DB_NAME} ensured on {config['host']}:{config['port']}")
            success = True
            break
        except Exception as e:
            print(f"❌ Failed to connect to {config['host']}:{config['port']}: {e}")
            continue
    
    return success

def init_tables():
    """Create all tables using SQLAlchemy"""
    try:
        print("🏗️  Initializing tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize tables: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🚀 INITIALIZING TIKTOK SENTIMENT ANALYSIS SYSTEM")
    print("="*60)
    
    if create_database():
        if init_tables():
            print("\n✨ Initialization complete! Ready to run.")
        else:
            print("\n⚠️ Database created but table initialization failed.")
    else:
        print("\n❌ Could not ensure database existence. Check your MySQL connection.")
