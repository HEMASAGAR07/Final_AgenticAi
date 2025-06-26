import os
from google.generativeai import configure, GenerativeModel
from dotenv import load_dotenv
import json

class TextProcessor:
    def __init__(self):
        load_dotenv()
        configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = GenerativeModel("gemini-1.5-flash")

    def summarize_medical_text(self, text, max_length=200):
        """Use LLM to create a concise medical summary"""
        try:
            if not text or len(str(text)) <= max_length:
                return text
                
            prompt = f"""
Summarize the following medical information concisely (maximum {max_length} characters) while preserving all important medical details:

{text}

Keep it professional and medically accurate. Include key symptoms, severity, and duration if mentioned.
"""
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            return summary[:max_length]
        except Exception as e:
            print(f"Warning: Error summarizing text: {str(e)}")
            return str(text)[:max_length]

    def build_mapping_prompt(self, raw_data, schema):
        """Build Gemini-compatible prompt for data mapping"""
        return f"""
You are an expert medical data mapper.

Given this database schema:

{schema}

And the following patient intake JSON:

{json.dumps(raw_data, indent=2)}

Map the data to this format, following valid table-column mappings only:

[
  {{
    "table": "patients",
    "columns": {{
      "full_name": "...",
      "age": ...,
      ...
    }}
  }},
  {{
    "table": "symptoms",
    "records": [
      {{
        "symptom_description": "...",
        "severity": "...",
        ...
      }},
      ...
    ]
  }}
]

Skip unrelated or unknown fields. Output valid JSON only.
""" 