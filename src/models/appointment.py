from datetime import datetime
import pymysql
from src.config.database import DatabaseConfig

class Appointment:
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = pymysql.connect(**self.db_config.get_config())
        self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_patient_id_by_email(self, email):
        self.cursor.execute("SELECT patient_id FROM patients WHERE email = %s", (email,))
        result = self.cursor.fetchone()
        return result['patient_id'] if result else None

    def check_slot_availability(self, doctor_id, appointment_date, appointment_time):
        self.cursor.execute("""
            SELECT 1 FROM appointments
            WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s
        """, (doctor_id, appointment_date, appointment_time))
        return not self.cursor.fetchone()

    def create_appointment(self, patient_id, doctor_id, appointment_date, appointment_time):
        self.cursor.execute("""
            INSERT INTO appointments 
            (patient_id, doctor_id, appointment_date, appointment_time, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, doctor_id, appointment_date, appointment_time, 1))
        self.conn.commit() 