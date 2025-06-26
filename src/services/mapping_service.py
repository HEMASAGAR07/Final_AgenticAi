import json
import sys
from datetime import datetime
from src.config.schema_manager import SchemaManager
from src.utils.date_utils import DateUtils
from src.utils.text_processor import TextProcessor

class MappingService:
    def __init__(self):
        self.schema_manager = SchemaManager()
        self.date_utils = DateUtils()
        self.text_processor = TextProcessor()

    def load_input_json(self, file_path):
        """Load the raw input JSON file"""
        with open(file_path, "r") as f:
            return json.load(f)

    def get_mapped_output(self, input_json):
        """Maps the collected information to the database schema"""
        try:
            patient_data = input_json.get("patient_data", {})
            mapped_output = []
            
            # Handle patient data
            patient_columns = {
                "full_name": patient_data.get("full_name", ""),
                "email": patient_data.get("email", ""),
                "phone": patient_data.get("phone", ""),
                "DOB": patient_data.get("DOB", ""),
                "gender": patient_data.get("gender", ""),
                "address": patient_data.get("address", "")
            }
            # Remove empty values
            patient_columns = {k: v for k, v in patient_columns.items() if v}
            if patient_columns:
                mapped_output.append({
                    "table": "patients",
                    "columns": patient_columns
                })

            # Handle symptoms
            symptoms_records = []
            
            # Process current symptoms
            current_symptoms = patient_data.get("current_symptoms", [])
            if isinstance(current_symptoms, list):
                for symptom in current_symptoms:
                    if isinstance(symptom, dict):
                        symptoms_records.append({
                            "symptom_description": symptom.get("description", ""),
                            "severity": symptom.get("severity", ""),
                            "duration": symptom.get("duration", ""),
                            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

            # Add appointment and doctor details
            if "selected_doctor" in patient_data and "appointment" in patient_data:
                doctor = patient_data["selected_doctor"]
                appt = patient_data["appointment"]
                
                # Add appointment record
                appointment_columns = {
                    "doctor_id": doctor.get("doctor_id"),
                    "appointment_date": self.date_utils.parse_date(appt.get("date")),
                    "appointment_time": appt.get("time"),
                    "status": 1  # 1 for scheduled
                }
                # Remove any None or empty values
                appointment_columns = {k: v for k, v in appointment_columns.items() if v is not None and v != ""}
                
                if appointment_columns:
                    mapped_output.append({
                        "table": "appointments",
                        "columns": appointment_columns
                    })
                
                # Add appointment notes to symptoms if needed
                symptoms_records.append({
                    "symptom_description": f"Scheduled appointment with Dr. {doctor.get('name')} ({doctor.get('specialization')}) at {doctor.get('hospital')} for {appt.get('date')} {appt.get('time')}",
                    "severity": "info",
                    "duration": "N/A",
                    "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

            # Add symptoms records if any exist
            if symptoms_records:
                mapped_output.append({
                    "table": "symptoms",
                    "records": symptoms_records
                })

            return mapped_output
        except Exception as e:
            raise Exception(f"Error mapping data: {str(e)}")

    def process_mapping(self, input_file, output_file="mapped_output.json"):
        """Process the mapping from input to output file"""
        try:
            raw_data = self.load_input_json(input_file)
        except FileNotFoundError:
            print(f" File not found: {input_file}")
            return
        except json.JSONDecodeError as e:
            print(f" Invalid JSON in input file: {str(e)}")
            return

        print(" Sending data to Gemini for mapping...")
        mapped_data = self.get_mapped_output(raw_data)

        if not mapped_data:
            print(" ❌ No valid mapped data generated")
            return

        try:
            with open(output_file, "w") as f:
                json.dump(mapped_data, f, indent=2, default=self.date_utils.date_serializer)
            print(f" ✅ Mapped output saved to: {output_file}")
            print(f" 📝 Generated {len(mapped_data)} table mappings")
        except Exception as e:
            print(f" ❌ Error saving mapped output: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print(" Please provide the input JSON file as an argument.")
        print(" Example: python mapping.py final_patient_summary.json")
        return

    mapping_service = MappingService()
    mapping_service.process_mapping(sys.argv[1])

if __name__ == "__main__":
    # Test the mapping
    mapping_service = MappingService()
    test_input = {
        "patient_data": {
            "full_name": "Test Patient",
            "DOB": "datetime.date(2003, 12, 13)",
            "email": "test@example.com"
        }
    }
    result = mapping_service.get_mapped_output(test_input)
    print(json.dumps(result, indent=2, default=DateUtils.date_serializer)) 