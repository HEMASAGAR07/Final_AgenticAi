import streamlit as st
import json
import google.generativeai as genai
from datetime import datetime
from src.utils.validation_utils import ValidationUtils
from src.services.db_operations import DatabaseOperations
from src.utils.session_manager import SessionManager
from src.services.medical_processor import MedicalProcessor

class MedicalIntakeService:
    def __init__(self):
        self.validation_utils = ValidationUtils()
        self.db_operations = DatabaseOperations()
        self.session_manager = SessionManager()

    def extract_json(self, text):
        """Extract JSON from model response"""
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
        except Exception as e:
            st.error(f"❌ JSON Parsing error: {e}")
        return {}

    def dynamic_medical_intake(self):
        """Handle the dynamic medical intake process"""
        # If symptoms have been collected, show the proceed button
        if st.session_state.symptoms_collected:
            
            return st.session_state.patient_data, "", True

        # If we're in health assessment, handle that flow
        if st.session_state.in_health_assessment:
            if st.session_state.intake_history:
                st.write(f"{st.session_state.intake_history[-1][1]}")

            user_input = st.text_input("Your answer:", key="intake_input", 
                                    placeholder="Type your response here...")
            submit = st.button("Continue", key="intake_submit")

            if submit and user_input:
                st.session_state.intake_history.append(("user", user_input))
                reply = st.session_state.intake_response.send_message(user_input)
                st.session_state.intake_history.append(("bot", reply.text.strip()))
                
                # Check if health intake is complete
                try:
                    final_output = self.extract_json(reply.text)
                    if final_output and isinstance(final_output, dict) and final_output.get("status") == "complete":
                        # Create a new patient data dictionary with existing and new data
                        updated_patient_data = st.session_state.patient_data.copy()
                        
                        # If there's new patient data in the final output, update our existing data
                        if "patient_data" in final_output and isinstance(final_output["patient_data"], dict):
                            updated_patient_data.update(final_output["patient_data"])
                        
                        # Store the updated data back in session state
                        st.session_state.patient_data = updated_patient_data
                        st.session_state.symptoms_collected = True

                        # Show success message and next steps
                        st.success("✅ Medical intake completed successfully!")
                        st.markdown("""
                        ### Next Steps
                        Based on your symptoms and health concerns, we will:
                        1. Analyze your symptoms
                        2. Recommend appropriate medical specialists
                        3. Help you schedule an appointment
                        """)
                        
                        # Add a progress spinner while transitioning
                        with st.spinner("Preparing specialist recommendations..."):
                            st.session_state.step = "specialist"
                            st.rerun()
                        
                        st.rerun()
                except Exception as e:
                    st.error(f"Error processing response: {str(e)}")
                st.rerun()
            return {}, "", False

        # Initial collection logic
        if st.session_state.intake_response is None:
            intro = """
You are MediBot, a medical intake assistant.

Ask for name FIRST:
- Start with: "Please enter your full name:"
- Validate name but don't show validation details
- After valid name, ask for email
- Keep it simple and direct
"""
            st.session_state.intake_response = genai.GenerativeModel("gemini-1.5-flash").start_chat(history=[])
            reply = st.session_state.intake_response.send_message(intro)
            st.session_state.intake_history.append(("bot", "Please enter your full name:"))
        else:
            reply = st.session_state.intake_response

        # If we have retrieved data but not confirmed it yet, show confirmation UI
        if st.session_state.db_data_retrieved and not st.session_state.data_confirmed:
            st.markdown("### Your Information")
            edit_mode = st.session_state.get('edit_details_mode', False)
            
            if st.session_state.is_new_patient:
                st.info("👋 Welcome! Here is your generated profile. Please review your details below.")
                patient = st.session_state.patient_data
                if not edit_mode:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("*Personal Details:*")
                        st.write(f"📝 Name: {patient.get('full_name', '')}")
                        st.write(f"📧 Email: {patient.get('email', '')}")
                        st.write(f"📱 Phone: {patient.get('phone', '')}")
                    with col2:
                        st.markdown("*Additional Information:*")
                        st.write(f"🎂 Date of Birth: {patient.get('DOB', '')}")
                        st.write(f"⚧ Gender: {patient.get('gender', '')}")
                        st.write(f"📍 Address: {patient.get('address', '')}")
                    col_btn1, col_btn2 = st.columns([1,1])
                    with col_btn1:
                        if st.button("Edit Details", key="edit_details_btn_new"):
                            st.session_state.edit_details_mode = True
                            st.rerun()
                    with col_btn2:
                        if st.button("Continue", key="dummy_profile_continue"):
                            st.session_state.data_confirmed = True
                            st.session_state.in_health_assessment = True
                            # Start health assessment with initial prompt
                            health_prompt = """
You are MediBot, a medical intake assistant. The patient has confirmed their details.

IMPORTANT RULES:
1. Start IMMEDIATELY with symptoms assessment
2. Accept and process ALL user responses, including simple yes/no answers
3. If user says "yes", follow up with specific questions about their symptoms
4. If user says "no", ask if they have any other health concerns
5. Never ignore user input or ask for clarification unnecessarily

CONVERSATION FLOW:
1. First Question: "What symptoms or health concerns are you experiencing today? If none, please say 'no'."

2. Based on Response:
   If symptoms mentioned:
   - Ask about severity (mild/moderate/severe)
   - Ask about duration
   - Ask about frequency
   
   If "yes":
   - Ask "Please describe your symptoms or health concerns."
   
   If "no":
   - Ask "Do you have any other health concerns you'd like to discuss?"

3. Follow-up Questions:
   - Keep questions specific and direct
   - Process every answer meaningfully
   - Don't repeat questions
   - Don't ignore simple answers

4. When Complete:
   Return a JSON object with this structure:
   {
     "status": "complete",
     "patient_data": {
       "current_symptoms": [
         {
           "description": "headache",
           "severity": "mild",
           "duration": "2 days"
         }
       ],
       "other_concerns": "none",
       "additional_notes": "patient reports good overall health"
     }
   }

Begin with: "What symptoms or health concerns are you experiencing today? If none, please say 'no'."
"""
                            st.session_state.intake_response = genai.GenerativeModel("gemini-1.5-flash").start_chat(history=[])
                            reply = st.session_state.intake_response.send_message(health_prompt)
                            st.session_state.intake_history = [("bot", reply.text.strip())]
                            st.session_state.edit_details_mode = False
                            st.rerun()
                else:
                    with st.form("edit_details_form_new"):
                        full_name = st.text_input("Full Name", value=patient.get('full_name', ''))
                        email = st.text_input("Email", value=patient.get('email', ''))
                        phone = st.text_input("Phone", value=patient.get('phone', ''))
                        dob = st.text_input("Date of Birth", value=patient.get('DOB', ''))
                        gender = st.text_input("Gender", value=patient.get('gender', ''))
                        address = st.text_area("Address", value=patient.get('address', ''))
                        submit_edit = st.form_submit_button("Save Changes")
                        if submit_edit:
                            st.session_state.patient_data.update({
                                'full_name': full_name,
                                'email': email,
                                'phone': phone,
                                'DOB': dob,
                                'gender': gender,
                                'address': address
                            })
                            st.session_state.edit_details_mode = False
                            st.rerun()
                    if st.button("Cancel Edit", key="cancel_edit_new"):
                        st.session_state.edit_details_mode = False
                        st.rerun()
                return {}, "", False
            else:
                # Show existing patient data
                patient_data = st.session_state.patient_data
                if not edit_mode:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("*Personal Details:*")
                        st.write(f"📝 Name: {patient_data.get('full_name', '')}")
                        st.write(f"📧 Email: {patient_data.get('email', '')}")
                        st.write(f"📱 Phone: {patient_data.get('phone', '')}")
                    with col2:
                        st.markdown("*Additional Information:*")
                        st.write(f"🎂 Date of Birth: {patient_data.get('DOB', '')}")
                        st.write(f"⚧ Gender: {patient_data.get('gender', '')}")
                        st.write(f"📍 Address: {patient_data.get('address', '')}")
                    # Show medical history if available
                    if any(key in patient_data for key in ['previous_symptoms', 'previous_medications', 'previous_allergies', 'previous_surgeries']):
                        st.markdown("### Previous Medical History")
                        if patient_data.get('previous_symptoms'):
                            st.write("🤒 Previous Symptoms:", patient_data['previous_symptoms'])
                        if patient_data.get('previous_medications'):
                            st.write("💊 Previous Medications:", patient_data['previous_medications'])
                        if patient_data.get('previous_allergies'):
                            st.write("⚠️ Known Allergies:", patient_data['previous_allergies'])
                        if patient_data.get('previous_surgeries'):
                            st.write("🏥 Previous Surgeries:", patient_data['previous_surgeries'])
                    st.info("👋 Welcome back! Please confirm your details are up to date.")
                    col_btn1, col_btn2 = st.columns([1,1])
                    with col_btn1:
                        if st.button("Edit Details", key="edit_details_btn_existing"):
                            st.session_state.edit_details_mode = True
                            st.rerun()
                    with col_btn2:
                        if st.button("✅ Confirm Details"):
                            st.session_state.data_confirmed = True
                            st.session_state.in_health_assessment = True
                            # Start health-specific questions immediately
                            health_prompt = """
You are MediBot, a medical intake assistant. The patient has confirmed their details.

IMPORTANT RULES:
1. Start IMMEDIATELY with symptoms assessment
2. Accept and process ALL user responses, including simple yes/no answers
3. If user says "yes", follow up with specific questions about their symptoms
4. If user says "no", ask if they have any other health concerns
5. Never ignore user input or ask for clarification unnecessarily

CONVERSATION FLOW:
1. First Question: "What symptoms or health concerns are you experiencing today? If none, please say 'no'."

2. Based on Response:
   If symptoms mentioned:
   - Ask about severity (mild/moderate/severe)
   - Ask about duration
   - Ask about frequency
   
   If "yes":
   - Ask "Please describe your symptoms or health concerns."
   
   If "no":
   - Ask "Do you have any other health concerns you'd like to discuss?"

3. Follow-up Questions:
   - Keep questions specific and direct
   - Process every answer meaningfully
   - Don't repeat questions
   - Don't ignore simple answers

4. When Complete:
   Return a JSON object with this structure:
   {
     "status": "complete",
     "patient_data": {
       "current_symptoms": [
         {
           "description": "headache",
           "severity": "mild",
           "duration": "2 days"
         }
       ],
       "other_concerns": "none",
       "additional_notes": "patient reports good overall health"
     }
   }

Begin with: "What symptoms or health concerns are you experiencing today? If none, please say 'no'."
"""
                            st.session_state.intake_response = genai.GenerativeModel("gemini-1.5-flash").start_chat(history=[])
                            reply = st.session_state.intake_response.send_message(health_prompt)
                            st.session_state.intake_history.append(("bot", reply.text.strip()))
                            st.session_state.edit_details_mode = False
                            st.rerun()
                else:
                    with st.form("edit_details_form_existing"):
                        full_name = st.text_input("Full Name", value=patient_data.get('full_name', ''))
                        email = st.text_input("Email", value=patient_data.get('email', ''))
                        phone = st.text_input("Phone", value=patient_data.get('phone', ''))
                        dob = st.text_input("Date of Birth", value=patient_data.get('DOB', ''))
                        gender = st.text_input("Gender", value=patient_data.get('gender', ''))
                        address = st.text_area("Address", value=patient_data.get('address', ''))
                        submit_edit = st.form_submit_button("Save Changes")
                        if submit_edit:
                            st.session_state.patient_data.update({
                                'full_name': full_name,
                                'email': email,
                                'phone': phone,
                                'DOB': dob,
                                'gender': gender,
                                'address': address
                            })
                            st.session_state.edit_details_mode = False
                            st.rerun()
                    if st.button("Cancel Edit", key="cancel_edit_existing"):
                        st.session_state.edit_details_mode = False
                        st.rerun()
                return {}, "", False

        # Only show the last bot message during initial collection
        if st.session_state.intake_history and not st.session_state.in_health_assessment:
            st.write(f"{st.session_state.intake_history[-1][1]}")

        user_input = st.text_input("Your answer:", key="intake_input", 
                                placeholder="Type your response here...")
        submit = st.button("Continue", key="intake_submit")

        if submit and user_input and not st.session_state.in_health_assessment:
            # Handle name input
            if st.session_state.current_field == "name":
                is_valid, result = self.validation_utils.is_valid_name(user_input)
                if not is_valid:
                    st.error(f"Invalid name: {result}")
                    return {}, "", False
                
                # Save name and move to email collection
                st.session_state.patient_data['full_name'] = result
                st.session_state.current_field = "email"
                st.session_state.intake_history.append(("bot", "Please enter your email:"))
                st.rerun()
                return {}, "", False
                
            # Handle email input
            elif st.session_state.current_field == "email":
                # Basic email validation
                if "@" not in user_input or "." not in user_input:
                    st.error("Please enter a valid email address.")
                    return {}, "", False
                
                # Save email and proceed
                st.session_state.patient_data['email'] = user_input
                st.session_state.initial_collection_done = True
                
                # Try to retrieve user data from DB
                try:
                    db_user_data = self.db_operations.get_user_from_db(user_input)
                    if db_user_data:
                        # Merge DB data with collected data
                        st.session_state.patient_data.update(db_user_data)
                        st.session_state.db_data_retrieved = True
                        st.session_state.is_new_patient = False
                        st.rerun()
                    else:
                        # This is a new patient: generate dummy data
                        processor = MedicalProcessor()
                        dummy_data = processor.generate_dummy_patient_data(user_input)
                        st.session_state.patient_data.update(dummy_data)
                        st.session_state.db_data_retrieved = True
                        st.session_state.is_new_patient = True
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error: {str(e)}")
                    return {}, "", False

        return {}, "", False 