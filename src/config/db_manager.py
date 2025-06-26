import os
import pymysql
import mysql.connector
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "charset": "utf8mb4",
            "use_unicode": True
        }

    def get_pymysql_connection(self):
        """Get a PyMySQL connection"""
        return pymysql.connect(**self.db_config)

    def get_mysql_connector(self):
        """Get a MySQL Connector connection with proper encoding"""
        return mysql.connector.connect(
            **self.db_config,
            collation="utf8mb4_unicode_ci"
        )

    def get_config(self):
        """Get the database configuration"""
        return self.db_config 