import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="MediBot - Smart Medical Assistant",
        page_icon="🏥",
        layout="centered",
        initial_sidebar_state="auto"
    )

def apply_custom_styling():
    st.markdown(
        """
        <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        }
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        }
        .stButton>button {
            background: linear-gradient(90deg, #6366f1 0%, #06b6d4 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6em 2em;
            font-size: 1.1em;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(99,102,241,0.08);
            transition: background 0.3s, box-shadow 0.3s;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #06b6d4 0%, #6366f1 100%);
            box-shadow: 0 4px 16px rgba(6,182,212,0.12);
        }
        .stTextInput>div>div>input, .stTextArea textarea {
            background: #f1f5f9;
            border: 1.5px solid #6366f1;
            border-radius: 6px;
            padding: 0.5em 1em;
            font-size: 1em;
        }
        .stTextInput>div>div>input:focus, .stTextArea textarea:focus {
            border: 2px solid #06b6d4;
            outline: none;
        }
        .stMarkdown, .stExpanderHeader, .stExpanderContent, .stAlert, .stSuccess, .stError, .stWarning {
            font-size: 1.08em;
        }
        .stExpander {
            background: #f1f5f9;
            border-radius: 10px;
            border: 1.5px solid #6366f1;
            margin-bottom: 1em;
        }
        .stExpanderHeader {
            color: #6366f1;
            font-weight: 700;
        }
        .stAlert, .stSuccess, .stError, .stWarning {
            border-radius: 8px;
            padding: 0.7em 1.2em;
        }
        .stSuccess {
            background: #d1fae5;
            color: #047857;
            border: 1.5px solid #10b981;
        }
        .stError {
            background: #fee2e2;
            color: #b91c1c;
            border: 1.5px solid #ef4444;
        }
        .stWarning {
            background: #fef9c3;
            color: #b45309;
            border: 1.5px solid #f59e42;
        }
        .stSidebar {
            background: #e0e7ff;
        }
        .stTitle {
            color: #6366f1;
            font-weight: 800;
            letter-spacing: 1px;
        }
        .stHeader {
            color: #06b6d4;
            font-weight: 700;
        }
        .stTable, .stDataFrame {
            background: #f1f5f9;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True
    ) 

class UIConfig:
    @classmethod
    def setup_page(cls):
        setup_page()

    @classmethod
    def apply_custom_styling(cls):
        apply_custom_styling() 