from src.config.db_manager import DatabaseManager
from src.models.data_operations import DataOperations
from src.utils.file_operations import FileOperations
from src.services.medical_processor import MedicalProcessor

class DataImportService:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.file_ops = FileOperations()
        self.medical_processor = MedicalProcessor()

    def insert_data_from_mapped_json(self, json_file_path):
        """Insert data from mapped JSON file into the database"""
        try:
            # Load the JSON file
            mapped_data = self.file_ops.load_json_file(json_file_path)
            
            if not isinstance(mapped_data, list):
                raise ValueError("Expected mapped data to be a list of table operations")
            
            # Connect to the database
            conn = self.db_manager.get_mysql_connector()
            cursor = conn.cursor()
            data_ops = DataOperations(cursor)

            patient_id = None
            
            # Process each table operation
            for table_op in mapped_data:
                table_name = table_op.get("table")
                if not table_name:
                    continue
                    
                if table_name == "patients":
                    # Insert patient data
                    columns = table_op.get("columns", {})
                    if columns:
                        data_ops.insert_single_record(table_name, columns)
                        patient_id = cursor.lastrowid
                
                elif table_name == "appointments" and patient_id:
                    # Insert appointment data
                    columns = table_op.get("columns", {})
                    if columns:
                        columns["patient_id"] = patient_id
                        data_ops.insert_single_record(table_name, columns)
                
                elif table_name == "symptoms" and patient_id:
                    # Insert symptoms data
                    records = table_op.get("records", [])
                    for record in records:
                        record["patient_id"] = patient_id
                        if "symptom_description" in record:
                            record["symptom_description"] = str(record["symptom_description"])[:65535]
                        data_ops.insert_single_record(table_name, record)

            # Commit the transaction
            conn.commit()
            return {"status": "success", "patient_id": patient_id}
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            raise Exception(f"Database error: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def recover_failed_operation(self, operation_id):
        """Recover from a failed operation"""
        state = self.file_ops.load_operation_state(operation_id)
        if not state:
            return {"status": "error", "message": "No recovery state found"}
        
        try:
            conn = self.db_manager.get_pymysql_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            data_ops = DataOperations(cursor)
            
            if state.get("error"):
                if state.get("patient_id"):
                    last_op = state.get("last_successful_operation")
                    if last_op and "original_data" in state:
                        data_ops.update_single_record(
                            "patients", 
                            state["original_data"]["columns"],
                            {"patient_id": state["patient_id"]}
                        )
                        return {
                            "status": "recovered",
                            "patient_id": state["patient_id"],
                            "last_successful": last_op
                        }
            
            return {"status": "error", "message": "Unable to recover"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    import_service = DataImportService()
    result = import_service.insert_data_from_mapped_json("mapped_output.json")
    print(result) 