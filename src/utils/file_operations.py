import json
import os

class FileOperations:
    @staticmethod
    def load_json_file(file_path):
        """Load and parse a JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error loading JSON file: {str(e)}")

    @staticmethod
    def save_operation_state(operation_id, state_data):
        """Save the state of a database operation"""
        try:
            state_file = f"operation_state_{operation_id}.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f)
            return True
        except:
            return False

    @staticmethod
    def load_operation_state(operation_id):
        """Load the state of a database operation"""
        try:
            state_file = f"operation_state_{operation_id}.json"
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None

    @staticmethod
    def load_mapped_output(file_path):
        """Load and validate the mapped JSON data"""
        try:
            with open(file_path, "r") as f:
                content = f.read().strip()
                print(f"📝 Raw file content: {content[:200]}...")
                
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error at position {e.pos}: {e.msg}")
                    print(f"Near text: {content[max(0, e.pos-20):min(len(content), e.pos+20)]}")
                    raise ValueError(f"Invalid JSON format: {str(e)}")

                if isinstance(data, (dict, list)):
                    return data
                else:
                    raise ValueError(f"Expected JSON object or array, got {type(data)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error loading mapped output: {str(e)}") 