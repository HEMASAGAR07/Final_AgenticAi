import streamlit as st
from src.agentic_workflow import graph, run_agentic_workflow  # ✅ Removed GraphContext
from src.config.ui_config import UIConfig
from src.services.medical_intake_service import MedicalIntakeService
from src.utils.session_manager import SessionManager
from src.services.db_operations import DatabaseOperations
from src.services.medical_processor import MedicalProcessor
from src.services.data_import_service import DataImportService
from src.services.mapping_service import MappingService
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import qrcode
from io import BytesIO

# Load environment variables
load_dotenv()

# Initialize services
medical_intake = MedicalIntakeService()
db_operations = DatabaseOperations()
medical_processor = MedicalProcessor()
data_import = DataImportService()
mapping_service = MappingService()

# Setup page configuration and styling
UIConfig.setup_page()
UIConfig.apply_custom_styling()

# Initialize session state
SessionManager.init_session_state()

if "agentic_state" not in st.session_state:
    st.session_state.agentic_state = "intake"

st.title("🏥 MediBot - Smart Medical Assistant (Agentic)")

# Intake State
if st.session_state.agentic_state == 'intake':
    st.markdown("### Medical Intake")
    patient_data, error, success = medical_intake.dynamic_medical_intake()
    if success:
        st.session_state.patient_data = patient_data
        st.success("✅ Medical intake completed successfully!")
        st.markdown("### Next Steps")
        st.markdown("Click below to get specialist recommendations based on your symptoms.")
        if st.button("Go to Specialist Recommendation", type="primary"):
            if 'current_symptoms' in patient_data:
                with st.spinner("Analyzing symptoms and finding appropriate specialists..."):
                    recommended_specializations = medical_processor.analyze_symptoms_and_recommend_specialists(
                        patient_data['current_symptoms']
                    )
                    if recommended_specializations:
                        st.session_state.recommended_specializations = recommended_specializations
                        st.session_state.agentic_state = 'specialist'
                        st.rerun()
                    else:
                        st.warning("Unable to determine specific specialists. Please consult with your primary care physician.")
                        st.session_state.recommended_specializations = None
                        st.stop()
            else:
                st.warning("No symptoms provided. Please complete the medical intake first.")
                st.session_state.recommended_specializations = None
                st.stop()

# Summary State
elif st.session_state.agentic_state == 'summary':
    st.markdown("### Summary")
    patient = st.session_state.get('patient_data', {})
    st.write(patient)
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Edit Details"):
            st.session_state.agentic_state = 'edit'
            st.rerun()
    with col2:
        if st.button("Continue"):
            st.session_state.agentic_state = 'specialist'
            st.rerun()

# Edit State
elif st.session_state.agentic_state == 'edit':
    st.markdown("### Edit Details")
    patient = st.session_state.get('patient_data', {})
    with st.form("edit_form"):
        full_name = st.text_input("Full Name", value=patient.get('full_name', ''))
        email = st.text_input("Email", value=patient.get('email', ''))
        submit = st.form_submit_button("Save Changes")
        if submit:
            st.session_state.patient_data = {'full_name': full_name, 'email': email}
            st.session_state.agentic_state = 'summary'
            st.rerun()
    if st.button("Cancel Edit"):
        st.session_state.agentic_state = 'summary'
        st.rerun()

# Specialist State
elif st.session_state.agentic_state == 'specialist':
    st.markdown("### Specialist Recommendation")
    if not st.session_state.recommended_specializations:
        st.success("Your medical intake is completed.")
        if st.button("Click here to get specialist"):
            st.session_state.agentic_state = 'intake'
            st.rerun()
        st.stop()
    doctors = db_operations.get_available_doctors(
        st.session_state.recommended_specializations
    )
    if not doctors:
        st.error(f"No {st.session_state.recommended_specializations[0]} available at the moment. Please try again later or consult with your primary care physician.")
        if st.button("Back to Intake"):
            st.session_state.agentic_state = 'intake'
            st.rerun()
        st.stop()
    st.markdown(f"#### Available {st.session_state.recommended_specializations[0]}s")
    for doctor in doctors:
        with st.expander(f"👨‍⚕️ Dr. {doctor.get('name', 'Unknown')} - {doctor.get('specialization', 'General')}"):
            st.write(f"**Experience:** {doctor.get('experience', 'N/A')} years")
            selected_date = st.date_input(
                "Select Appointment Date",
                value=datetime.now().date(),
                min_value=datetime.now().date(),
                max_value=datetime.now().date() + timedelta(days=365),
                key=f"date_{doctor['doctor_id']}"
            )
            if selected_date != st.session_state.selected_date:
                st.session_state.selected_date = selected_date
                SessionManager.handle_date_change()
            slots = db_operations.get_all_slots_status(doctor['doctor_id'], selected_date)
            if slots:
                st.markdown("#### ⏰ Available Time Slots")
                st.success(f"✅ {len(slots)} time slots available")
                cols = st.columns(3)
                for i, slot in enumerate(slots):
                    with cols[i % 3]:
                        try:
                            time_obj = datetime.strptime(slot, "%H:%M")
                            display_time = time_obj.strftime("%I:%M %p").lstrip("0")
                        except ValueError:
                            display_time = slot
                        if st.button(display_time, key=f"slot_{doctor['doctor_id']}_{slot}"):
                            st.session_state.last_doctor = {
                                'id': doctor['doctor_id'],
                                'name': doctor.get('name', 'Unknown'),
                                'specialization': doctor.get('specialization', 'General')
                            }
                            st.session_state.last_selected_slot = slot
                            st.session_state.last_selected_date = selected_date
                            st.session_state.show_save_button = True
                            st.rerun()
            else:
                st.warning("👉 No available slots for the selected date. Please choose a different date.")
            if st.session_state.get('show_save_button', False):
                st.markdown("---")
                st.markdown("### Confirm Appointment")
                st.markdown(f"""
                Selected Appointment Details:
                - **Doctor:** Dr. {st.session_state.last_doctor['name']}
                - **Specialization:** {st.session_state.last_doctor['specialization']}
                - **Date:** {st.session_state.last_selected_date}
                - **Time:** {st.session_state.last_selected_slot}
                """)
                if st.button("Save to Database", type="primary"):
                    try:
                        success = db_operations.save_appointment_to_db(
                            st.session_state.last_doctor['id'],
                            st.session_state.last_selected_date,
                            st.session_state.last_selected_slot,
                            st.session_state.patient_data.get('email', '')
                        )
                        if success:
                            st.success("✅ Appointment saved successfully!")
                            appointment_details = {
                                'patient_name': st.session_state.patient_data.get('full_name', ''),
                                'date': st.session_state.last_selected_date.strftime("%Y-%m-%d"),
                                'time': st.session_state.last_selected_slot,
                                'doctor_name': st.session_state.last_doctor['name'],
                                'specialization': st.session_state.last_doctor['specialization']
                            }
                            st.session_state.appointment_details = appointment_details
                            st.session_state.show_save_button = False
                            st.session_state.last_doctor = None
                            st.session_state.last_selected_slot = None
                            st.session_state.last_selected_date = None
                            st.session_state.agentic_state = 'confirmation'
                            st.rerun()
                        else:
                            st.error("❌ Failed to save appointment. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Error saving appointment: {str(e)}")

# Booking State
elif st.session_state.agentic_state == 'booking':
    st.markdown("### Book Appointment")
    if st.button("Confirm Appointment"):
        st.session_state.agentic_state = 'confirmation'
        st.rerun()

# Confirmation State
elif st.session_state.agentic_state == 'confirmation':
    st.success("### ✅ Appointment Confirmed!")
    patient = st.session_state.get('patient_data', {})
    appointment = st.session_state.get('appointment_details', {})
    st.markdown(f"""
    Your appointment has been successfully booked. Here's a summary:
    - **Patient:** {patient.get('full_name', '')}
    - **Date:** {appointment.get('date', '')}
    - **Time:** {appointment.get('time', '')}
    - **Doctor:** {appointment.get('doctor_name', '')}
    - **Specialization:** {appointment.get('specialization', '')}
    """)
    qr_summary = f"Appointment for {patient.get('full_name', '')}\\nDate: {appointment.get('date', '')}\\nTime: {appointment.get('time', '')}\\nDoctor: {appointment.get('doctor_name', '')}\\nSpecialization: {appointment.get('specialization', '')}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_summary)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf.getvalue(), caption="Scan to save/share your appointment details", use_column_width=False)
    if st.button("Start New Intake"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        SessionManager.init_session_state()
        st.session_state.agentic_state = 'intake'
        st.rerun() 