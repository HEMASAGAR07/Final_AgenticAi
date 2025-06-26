import google.generativeai as genai
import os
from dotenv import load_dotenv
import streamlit as st

class MedicalProcessor:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Missing API key. Set GOOGLE_API_KEY in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def verify_medical_terms(self, terms, term_type):
        """Verify medical terms against standard vocabulary"""
        if term_type == "medication":
            # Check if medication terms contain units (mg, ml, g)
            return any(unit in terms.lower() for unit in ["mg", "ml", "g"])
        elif term_type == "symptom":
            # Check if symptom terms are longer than 3 characters
            return len(terms) > 3
        return True

    def summarize_symptom_description(self, description, max_length=200):
        """Summarize long symptom descriptions"""
        try:
            prompt = f"""
            Summarize the following medical symptom description in {max_length} characters or less:
            {description}
            
            Keep important medical terms and severity indicators.
            """
            response = self.model.generate_content(prompt)
            return response.text[:max_length]
        except Exception as e:
            print(f"Error summarizing symptoms: {e}")
            return description[:max_length]

    def analyze_symptoms_and_recommend_specialists(self, symptoms_data):
        """Analyze symptoms and recommend appropriate specialists"""
        try:
            # Prepare symptoms data for analysis
            symptoms_text = ""
            if isinstance(symptoms_data, list):
                for symptom in symptoms_data:
                    if isinstance(symptom, dict):
                        symptoms_text += f"- {symptom.get('description', '')} "
                        symptoms_text += f"(Severity: {symptom.get('severity', 'unknown')}, "
                        symptoms_text += f"Duration: {symptom.get('duration', 'unknown')})\n"
                    else:
                        symptoms_text += f"- {symptom}\n"
            elif isinstance(symptoms_data, str):
                symptoms_text = symptoms_data

            # Create prompt for specialist recommendation
            prompt = f"""
You are a medical triage assistant.

Based on the following patient data, recommend the most appropriate medical specialist(s) for consultation.

Patient data:
{symptoms_text}

Instructions:
- Analyze symptoms, medical history, medications, allergies, and other relevant information.
- Recommend 1 or more specialist types (e.g., Cardiologist, Neurologist, Dermatologist, Orthopedic Surgeon, etc.)
- Provide a brief rationale for the recommendation.
- Return ONLY a JSON object with this format:

{{
  "recommended_specialist": ["Specialist Name 1", "Specialist Name 2"],
  "rationale": "Short explanation why these specialists are recommended.",
  "status": "done"
}}
"""
            # Get recommendation from the model
            response = self.model.generate_content(prompt)
            recommended_specializations = response.text.strip()

            # Extract JSON from response
            try:
                import json
                import re
                
                # Find JSON in the response
                json_match = re.search(r'\{.*\}', recommended_specializations, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if result.get("status") == "done":
                        # Store rationale in session state for display
                        st.session_state.specialist_rationale = result.get("rationale", "")
                        return result.get("recommended_specialist", [])
            except (json.JSONDecodeError, AttributeError):
                pass

            return []

        except Exception as e:
            print(f"Error analyzing symptoms: {e}")
            return []

    def generate_dummy_patient_data(self, email):
        """Generate a realistic fake patient profile using LLM for a given email."""
        import json
        prompt = f"""
Generate a realistic but fake patient profile as a JSON object for the following email: {email}.
Include: full_name, age, gender, address, phone, DOB (YYYY-MM-DD), and use the email provided.
Return only the JSON object.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                data['email'] = email  # Ensure email is set
                return data
        except Exception as e:
            print(f"Error generating dummy patient data: {e}")
        # Fallback dummy data
        from datetime import date
        return {
            'full_name': 'Guest User',
            'age': 30,
            'gender': 'Other',
            'address': '123 Main St, City',
            'phone': '0000000000',
            'DOB': str(date.today().replace(year=date.today().year-30)),
            'email': email
        } 