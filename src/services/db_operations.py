import pymysql
import json
from datetime import datetime
from src.config.db_manager import DatabaseManager
import streamlit as st
from src.services.medical_processor import MedicalProcessor

class DatabaseOperations:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_config = self.db_manager.get_config()

    def get_user_from_db(self, email):
        """Retrieve user data from database using email"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # First get patient basic info
            cursor.execute("""
                SELECT 
                    p.patient_id,
                    p.full_name,
                    p.age,
                    p.gender,
                    p.email,
                    p.phone,
                    p.address,
                    p.DOB
                FROM patients p
                WHERE p.email = %s
            """, (email,))
            
            user_data = cursor.fetchone()
            if user_data:
                # Convert to regular dict and clean up None values
                user_data = dict(user_data)
                
                # Get symptoms
                cursor.execute("""
                    SELECT GROUP_CONCAT(
                        CONCAT(symptom_description, ' (', severity, ', ', duration, ')')
                    ) as symptoms_list
                    FROM symptoms 
                    WHERE patient_id = %s
                """, (user_data['patient_id'],))
                symptoms_result = cursor.fetchone()
                user_data['previous_symptoms'] = symptoms_result['symptoms_list'] if symptoms_result and symptoms_result['symptoms_list'] else ""
                
                # Get medications
                cursor.execute("""
                    SELECT GROUP_CONCAT(
                        CONCAT(medication_name, ' (', dosage, ')')
                    ) as medications_list
                    FROM medications 
                    WHERE patient_id = %s
                """, (user_data['patient_id'],))
                medications_result = cursor.fetchone()
                user_data['previous_medications'] = medications_result['medications_list'] if medications_result and medications_result['medications_list'] else ""
                
                # Get allergies
                cursor.execute("""
                    SELECT GROUP_CONCAT(
                        CONCAT(substance, ' (', severity, ')')
                    ) as allergies_list
                    FROM allergies 
                    WHERE patient_id = %s
                """, (user_data['patient_id'],))
                allergies_result = cursor.fetchone()
                user_data['previous_allergies'] = allergies_result['allergies_list'] if allergies_result and allergies_result['allergies_list'] else ""
                
                # Get surgeries
                cursor.execute("""
                    SELECT GROUP_CONCAT(
                        CONCAT(procedure_name, ' at ', hospital_name, ' on ', surgery_date)
                    ) as surgeries_list
                    FROM surgeries 
                    WHERE patient_id = %s
                """, (user_data['patient_id'],))
                surgeries_result = cursor.fetchone()
                user_data['previous_surgeries'] = surgeries_result['surgeries_list'] if surgeries_result and surgeries_result['surgeries_list'] else ""
                
                # Clean up None values
                for key in user_data:
                    if user_data[key] is None:
                        user_data[key] = ""
            
            return user_data
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_available_doctors(self, specializations=None):
        """Get list of available doctors with their booked slots"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Base query
            query = """
                SELECT 
                    d.doctor_id,
                    d.full_name as name,
                    d.specialization,
                    d.experience_years as experience,
                    d.available_slots
                FROM doctors d
            """
            
            # Add specialization filter if provided
            params = []
            if specializations and isinstance(specializations, list):
                # Get only the first (most relevant) specialization
                primary_specialization = specializations[0]
                query += " WHERE d.specialization = %s"
                params.append(primary_specialization)
            
            query += " ORDER BY d.full_name"
            
            # Execute query
            cursor.execute(query, params)
            doctors = cursor.fetchall()
            
            # Process each doctor's data
            for doctor in doctors:
                # Convert available_slots from JSON string to list
                if doctor['available_slots']:
                    try:
                        available_slots = json.loads(doctor['available_slots'])
                        # Sort the slots for better display
                        available_slots.sort()
                        doctor['available_slots'] = available_slots
                    except json.JSONDecodeError:
                        doctor['available_slots'] = []
                else:
                    doctor['available_slots'] = []
            
            return doctors
            
        except Exception as e:
            st.error(f"Error fetching doctors: {str(e)}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_all_slots_status(self, doctor_id, date):
        """Get all slots status for a specific doctor and date"""
        connection = pymysql.connect(**self.db_config, cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                # Fetch available and booked slots
                cursor.execute("""
                    SELECT 
                        d.available_slots,
                        GROUP_CONCAT(
                            DISTINCT a.appointment_time
                        ) as booked_slots
                    FROM doctors d
                    LEFT JOIN appointments a ON d.doctor_id = a.doctor_id 
                        AND a.status = 1
                        AND a.appointment_date = %s
                    WHERE d.doctor_id = %s
                    GROUP BY d.doctor_id
                """, (date, doctor_id))

                result = cursor.fetchone()

                # Step 1: Parse available slots from DB
                available_slots = []
                if result and result['available_slots']:
                    try:
                        available_slots = json.loads(result['available_slots'])
                    except json.JSONDecodeError:
                        return []
                else:
                    return []

                # Step 2: Parse booked slots
                booked_slots = set()
                if result and result['booked_slots']:
                    # Convert booked slots to HH:MM format
                    booked_times = result['booked_slots'].split(',')
                    for time in booked_times:
                        try:
                            # Remove seconds from time format (HH:MM:SS -> HH:MM)
                            time_str = time.split(':')[0] + ':' + time.split(':')[1]
                            booked_slots.add(time_str)
                        except (ValueError, TypeError, IndexError):
                            continue

                # Step 3: Filter available slots
                final_slots = [slot for slot in available_slots if slot not in booked_slots]
                final_slots.sort()

                return final_slots

        except Exception as e:
            st.error(f"Error getting slots status: {str(e)}")
            return []
        finally:
            connection.close()

    def reserve_appointment_slot(self, doctor_id, appointment_date, appointment_time, email):
        """Reserve an appointment slot in the database"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("START TRANSACTION")
            
            # Check if slot is already booked
            cursor.execute("""
                SELECT COUNT(*) 
                FROM appointments 
                WHERE doctor_id = %s
                AND appointment_date = %s 
                AND appointment_time = %s
                AND status = 1
            """, (doctor_id, appointment_date, appointment_time))
            
            if cursor.fetchone()[0] > 0:
                cursor.execute("ROLLBACK")
                return False, "This slot is already booked."
            
            # Get patient_id from email
            cursor.execute("SELECT patient_id FROM patients WHERE email = %s", (email,))
            result = cursor.fetchone()
            if not result:
                cursor.execute("ROLLBACK")
                return False, "Patient not found. Please complete registration first."
            
            patient_id = result[0]
            
            # Check if patient already has an appointment at this time
            cursor.execute("""
                SELECT COUNT(*) 
                FROM appointments 
                WHERE patient_id = %s
                AND appointment_date = %s 
                AND appointment_time = %s
                AND status = 1
            """, (patient_id, appointment_date, appointment_time))
            
            if cursor.fetchone()[0] > 0:
                cursor.execute("ROLLBACK")
                return False, "You already have an appointment at this time."
            
            # Insert the appointment
            cursor.execute("""
                INSERT INTO appointments 
                (doctor_id, patient_id, appointment_date, appointment_time, status) 
                VALUES (%s, %s, %s, %s, 1)
            """, (doctor_id, patient_id, appointment_date, appointment_time))
            
            cursor.execute("COMMIT")
            return True, "Appointment slot reserved successfully!"
        except Exception as e:
            if 'cursor' in locals():
                cursor.execute("ROLLBACK")
            return False, f"Error reserving slot: {str(e)}"
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_appointment_to_db(self, doctor_id, appointment_date, appointment_time, patient_email):
        """Save appointment to database"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            # First get or create the patient
            cursor.execute("SELECT patient_id FROM patients WHERE email = %s", (patient_email,))
            patient_result = cursor.fetchone()
            if not patient_result:
                # Use LLM to generate dummy patient data
                processor = MedicalProcessor()
                dummy_data = processor.generate_dummy_patient_data(patient_email)
                cursor.execute("""
                    INSERT INTO patients (full_name, age, gender, email, phone, address, DOB)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    dummy_data.get('full_name', ''),
                    dummy_data.get('age', 30),
                    dummy_data.get('gender', 'Other'),
                    dummy_data.get('email', patient_email),
                    dummy_data.get('phone', '0000000000'),
                    dummy_data.get('address', ''),
                    dummy_data.get('DOB', '1990-01-01')
                ))
                patient_id = cursor.lastrowid
                # Update session state with dummy data
                st.session_state.patient_data = dummy_data
            else:
                patient_id = patient_result['patient_id']
            # Convert appointment_time to proper TIME format
            try:
                hours, minutes = map(int, appointment_time.split(':'))
                time_str = f"{hours:02d}:{minutes:02d}:00"
            except ValueError:
                raise Exception("Invalid time format")
            # Check if the slot is already booked for this specific date
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM appointments
                WHERE doctor_id = %s
                AND appointment_date = %s
                AND appointment_time = %s
                AND status = 1
            """, (doctor_id, appointment_date, time_str))
            if cursor.fetchone()['count'] > 0:
                raise Exception("This slot is already booked for this date")
            # Insert the appointment with status = 1 (confirmed)
            cursor.execute("""
                INSERT INTO appointments 
                (patient_id, doctor_id, appointment_date, appointment_time, status)
                VALUES (%s, %s, %s, %s, 1)
            """, (patient_id, doctor_id, appointment_date, time_str))
            conn.commit()
            return True
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            raise Exception(f"Error saving appointment: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def convert_time_format(time_str):
        """Convert time string to 24-hour format (HH:MM)"""
        try:
            # If time is already in 24-hour format
            if ":" in time_str and not any(x in time_str.upper() for x in ["AM", "PM"]):
                # Ensure consistent format HH:MM
                time_parts = time_str.split(":")
                if len(time_parts) == 2:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        return f"{hours:02d}:{minutes:02d}"
                return None
            
            # Convert 12-hour format to 24-hour
            try:
                time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")
                return time_obj.strftime("%H:%M")
            except ValueError:
                # Try alternative format without leading zeros
                time_obj = datetime.strptime(time_str.strip(), "%-I:%M %p")
                return time_obj.strftime("%H:%M")
        except Exception as e:
            raise Exception(f"Time conversion error for '{time_str}': {str(e)}") 