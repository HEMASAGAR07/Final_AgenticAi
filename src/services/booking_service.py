import json
from datetime import datetime, timedelta
from src.models.appointment import Appointment
from src.utils.day_parser import DayParser

class BookingService:
    def __init__(self):
        self.appointment = Appointment()
        self.day_parser = DayParser()

    def book_appointment_from_json(self, json_file_path="final_patient_summary.json"):
        try:
            with open(json_file_path) as f:
                data = json.load(f)

            recommended_specialists = data.get("recommended_specialist", [])
            patient_email = data["patient_data"].get("email")

            if not patient_email:
                raise ValueError("Patient email not found in JSON.")

            self.appointment.connect()
            patient_id = self.appointment.get_patient_id_by_email(patient_email)
            
            if not patient_id:
                raise ValueError(f"Patient with email {patient_email} not found in database.")

            for specialist in recommended_specialists:
                self.appointment.cursor.execute(
                    "SELECT * FROM doctors WHERE specialization = %s", 
                    (specialist,)
                )
                doctors = self.appointment.cursor.fetchall()
                
                if not doctors:
                    continue

                for doctor in doctors:
                    available_days = self.day_parser.parse_available_days(doctor["available_days"])
                    try:
                        available_slots = json.loads(doctor["available_slots"])
                    except Exception:
                        continue

                    for i in range(7):
                        check_date = datetime.today() + timedelta(days=i)
                        weekday = check_date.strftime('%A')

                        if weekday in available_days:
                            for slot in available_slots:
                                slot_time = slot if len(slot) == 8 else slot + ":00"

                                if self.appointment.check_slot_availability(
                                    doctor["doctor_id"], 
                                    check_date.date(), 
                                    slot_time
                                ):
                                    self.appointment.create_appointment(
                                        patient_id,
                                        doctor["doctor_id"],
                                        check_date.date(),
                                        slot_time
                                    )
                                    return f"Appointment booked with Dr. {doctor['full_name']} on {check_date.date()} at {slot_time}"

            return "No available slots found for any recommended specialist in the next 7 days."

        finally:
            self.appointment.close()

if __name__ == "__main__":
    booking_service = BookingService()
    print(booking_service.book_appointment_from_json()) 