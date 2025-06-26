from config.database import DatabaseConfig
import pymysql

def test_database_connection():
    try:
        # Get database configuration
        db_config = DatabaseConfig()
        config = db_config.get_config()
        
        # Try to establish connection
        print("Attempting to connect to database...")
        print(f"Host: {config['host']}")
        print(f"Database: {config['database']}")
        print(f"Port: {config['port']}")
        
        connection = pymysql.connect(**config)
        
        # Test the connection by executing a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print("\nConnection successful!")
            print(f"Database version: {version[0]}")
            
            # Test if we can access the tables
            print("\nChecking tables...")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("Available tables:")
            for table in tables:
                print(f"- {table[0]}")
                
    except Exception as e:
        print("\nError connecting to database:")
        print(f"Error message: {str(e)}")
    finally:
        if 'connection' in locals():
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    test_database_connection() 