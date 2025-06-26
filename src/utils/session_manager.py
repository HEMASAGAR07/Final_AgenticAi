import streamlit as st
from datetime import datetime

class SessionManager:
    @staticmethod
    def init_session_state():
        """Initialize session state variables"""
        if "step" not in st.session_state:
            st.session_state.step = "intake"
        if "form_key" not in st.session_state:
            st.session_state.form_key = 0
        if "selected_date" not in st.session_state:
            st.session_state.selected_date = datetime.now().date()
        if "last_doctor" not in st.session_state:
            st.session_state.last_doctor = None
        if "last_selected_slot" not in st.session_state:
            st.session_state.last_selected_slot = None
        if "last_selected_date" not in st.session_state:
            st.session_state.last_selected_date = None
        if "show_save_button" not in st.session_state:
            st.session_state.show_save_button = False
        if "patient_data" not in st.session_state:
            st.session_state.patient_data = {}
        if "symptoms_collected" not in st.session_state:
            st.session_state.symptoms_collected = False
        if "recommended_specializations" not in st.session_state:
            st.session_state.recommended_specializations = []
        if "specialist_rationale" not in st.session_state:
            st.session_state.specialist_rationale = ""
        if "appointment_date_key" not in st.session_state:
            st.session_state.appointment_date_key = 0
        if "error_message" not in st.session_state:
            st.session_state.error_message = None
        if "intake_history" not in st.session_state:
            st.session_state.intake_history = []
        if "intake_response" not in st.session_state:
            st.session_state.intake_response = None
        if "initial_collection_done" not in st.session_state:
            st.session_state.initial_collection_done = False
        if "db_data_retrieved" not in st.session_state:
            st.session_state.db_data_retrieved = False
        if "current_field" not in st.session_state:
            st.session_state.current_field = "name"
        if "data_confirmed" not in st.session_state:
            st.session_state.data_confirmed = False
        if "in_health_assessment" not in st.session_state:
            st.session_state.in_health_assessment = False
        if "is_new_patient" not in st.session_state:
            st.session_state.is_new_patient = None
        if "selected_doctor" not in st.session_state:
            st.session_state.selected_doctor = None
        if "followup_history" not in st.session_state:
            st.session_state.followup_history = []
        if "followup_response" not in st.session_state:
            st.session_state.followup_response = None
        if "confirm_response" not in st.session_state:
            st.session_state.confirm_response = None
        if "confirm_history" not in st.session_state:
            st.session_state.confirm_history = []
        if "updated_final_data" not in st.session_state:
            st.session_state.updated_final_data = {}
        if "db_cache" not in st.session_state:
            st.session_state.db_cache = {}
        if "appointment_details" not in st.session_state:
            st.session_state.appointment_details = {
                'patient_name': '',
                'date': '',
                'time': '',
                'doctor_name': '',
                'specialization': ''
            }

    @staticmethod
    def handle_date_change():
        """Handle date change event"""
        # Increment form key to force refresh
        st.session_state.form_key = st.session_state.get('form_key', 0) + 1
        st.session_state.appointment_date_key += 1
        # Clear previous selections
        if 'selected_time_24h' in st.session_state:
            del st.session_state.selected_time_24h

    @staticmethod
    def invalidate_user_cache(email):
        """Invalidate cached data for a user"""
        if "db_cache" in st.session_state:
            cache_key = f"user_data_{email}"
            if cache_key in st.session_state.db_cache:
                del st.session_state.db_cache[cache_key]

    @staticmethod
    def migrate_existing_data(data):
        """Migrate existing data to new format, ensuring all required fields exist."""
        if not isinstance(data, dict):
            return data

        if "patient_data" in data:
            patient_data = data["patient_data"]
            
            # Move address from notes if it exists and address is empty
            if "notes" in patient_data and not patient_data.get("address"):
                patient_data["address"] = patient_data["notes"]
                patient_data["notes"] = ""
            
            # Ensure email field exists
            if "email" not in patient_data:
                patient_data["email"] = ""
                
            # Ensure other required fields exist
            required_fields = ["name", "email", "dob", "gender", "phone", "address"]
            for field in required_fields:
                if field not in patient_data:
                    patient_data[field] = ""
                    
            data["patient_data"] = patient_data
        
        return data 