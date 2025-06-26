import json
import os
from datetime import datetime

class DataOperations:
    def __init__(self, cursor):
        self.cursor = cursor

    def insert_single_record(self, table, columns):
        """Insert a single record into a table"""
        col_names = ", ".join([f"`{key}`" for key in columns.keys()])
        placeholders = ", ".join(["%s"] * len(columns))
        values = list(columns.values())
        query = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"
        print(f"🔍 Executing query: {query}")
        print(f"🔍 With values: {values}")
        self.cursor.execute(query, values)

    def insert_multiple_records(self, table, records):
        """Insert multiple records into a table"""
        if not records:
            return
        col_names = ", ".join([f"`{key}`" for key in records[0].keys()])
        placeholders = ", ".join(["%s"] * len(records[0]))
        query = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"
        values = [tuple(rec.values()) for rec in records]
        print(f"🔍 Executing query: {query}")
        print(f"🔍 With values: {values}")
        self.cursor.executemany(query, values)

    def update_single_record(self, table, columns, where_clause):
        """Update an existing record in the database"""
        set_clause = ", ".join([f"`{key}` = %s" for key in columns.keys()])
        where_str = " AND ".join([f"`{key}` = %s" for key in where_clause.keys()])
        query = f"UPDATE `{table}` SET {set_clause} WHERE {where_str}"
        values = list(columns.values()) + list(where_clause.values())
        print(f"🔄 Executing update query: {query}")
        print(f"🔄 With values: {values}")
        self.cursor.execute(query, values)
        return self.cursor.rowcount

    def update_multiple_records(self, table, records, patient_id, record_type):
        """Update or insert multiple records for a patient"""
        self.cursor.execute(f"DELETE FROM {table} WHERE patient_id = %s", (patient_id,))
        if records:
            for record in records:
                record['patient_id'] = patient_id
            col_names = ", ".join([f"`{key}`" for key in records[0].keys()])
            placeholders = ", ".join(["%s"] * len(records[0]))
            query = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"
            values = [tuple(rec.values()) for rec in records]
            print(f"🔄 Executing {record_type} update query: {query}")
            print(f"🔄 With values: {values}")
            self.cursor.executemany(query, values)
        return self.cursor.rowcount

    def check_patient_exists(self, email):
        """Check if a patient exists and get their ID"""
        self.cursor.execute("SELECT patient_id FROM patients WHERE email = %s", (email,))
        result = self.cursor.fetchone()
        return result['patient_id'] if result else None

    def get_last_update_timestamp(self, patient_id):
        """Get the last update timestamp for a patient"""
        self.cursor.execute("SELECT last_updated FROM patients WHERE patient_id = %s", (patient_id,))
        result = self.cursor.fetchone()
        return result['last_updated'] if result else None

    def update_patient_timestamp(self, patient_id):
        """Update the last_updated timestamp for a patient"""
        self.cursor.execute(
            "UPDATE patients SET last_updated = CURRENT_TIMESTAMP WHERE patient_id = %s",
            (patient_id,)
        ) 