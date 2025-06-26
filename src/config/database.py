import os
from dotenv import load_dotenv

class DatabaseConfig:
    def __init__(self):
        load_dotenv()
        self.config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "port": int(os.getenv("DB_PORT", 3306))
        }
    
    def get_config(self):
        return self.config 