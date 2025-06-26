from langgraph.graph import StateGraph
from src.services.medical_processor import MedicalProcessor

# Define the state structure
def agent_decide_next_step(state):
    """
    Simulate an LLM/agent deciding the next state based on the current state and data.
    In a real system, this would call an LLM with a prompt.
    """
    # For demo: if patient_data has 'needs_edit', go to edit, else specialist
    if state.get('patient_data', {}).get('needs_edit'):
        return 'edit'
    return 'specialist'

# Define the functions for each state

def intake_state(state):
    print("Running Intake...")
    # Intake logic (could be LLM-driven)
    state['patient_data'] = {'name': 'John Doe', 'symptoms': 'cough', 'needs_edit': False}
    return 'summary', state

def summary_state(state):
    print("Showing Summary...")
    # Agent/LLM decides what to do next
    next_state = agent_decide_next_step(state)
    print(f"Agent decided next state: {next_state}")
    return next_state, state

def edit_state(state):
    print("Editing details...")
    # Edit logic (could be LLM-driven)
    state['patient_data']['name'] = 'Jane Doe'  # Simulate edit
    state['patient_data']['needs_edit'] = False
    return 'summary', state

def specialist_state(state):
    print("Specialist recommendation...")
    # Use LLM/agent to recommend specialist
    processor = MedicalProcessor()
    # Simulate LLM/agent call
    specialist = processor.analyze_symptoms_and_recommend_specialists(state['patient_data'].get('symptoms', ''))
    state['specialist'] = specialist if specialist else 'General Physician'
    return 'booking', state

def booking_state(state):
    print("Booking appointment...")
    # Booking logic (could be LLM-driven)
    state['appointment'] = '10 AM, 1st July'
    return 'confirmation', state

def confirmation_state(state):
    print("Confirmation...")
    print("Summary:", state)
    return None, state  # End of the workflow

# Build the graph
builder = StateGraph(dict)

# Add nodes
builder.add_node('intake', intake_state)
builder.add_node('summary', summary_state)
builder.add_node('edit', edit_state)
builder.add_node('specialist', specialist_state)
builder.add_node('booking', booking_state)
builder.add_node('confirmation', confirmation_state)

# Add edges (transitions)
builder.add_edge('intake', 'summary')
builder.add_edge('summary', 'edit')
builder.add_edge('summary', 'specialist')
builder.add_edge('edit', 'summary')
builder.add_edge('specialist', 'booking')
builder.add_edge('booking', 'confirmation')

# Set start and end
builder.set_entry_point('intake')
builder.set_finish_point('confirmation')

# Compile the graph
graph = builder.compile()

# Function to run the graph
def run_agentic_workflow(initial_data=None):
    state = initial_data or {}
    for event in graph.stream(state):
        state = event["state"]
        if event["next"] is None:
            break
    return state

# ✅ Example Run
if __name__ == "__main__":
    final_data = run_agentic_workflow()
    print("Final Data:", final_data)
