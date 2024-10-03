import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from datetime import datetime

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0.5, model_name="gpt-4o", openai_api_key=openai_api_key)

def process_meeting_notes(notes: str, user_bio: str):
    system_prompt = """You are a helpful assistant that extracts key information from meeting notes and provides networking suggestions."""

    user_prompt = f"""
    Given the following user biography and meeting notes, extract the requested information and provide networking suggestions:
    
    User biography: {user_bio}
    Meeting notes: {notes}

    Output your answer as a JSON object with the following format:
    {{
        "name": "First and Last Name",
        "job": "Job Title or Profession",
        "last_seen": "YYYY-MM-DD",
        "context": "Additional information about the person",
        "networking_suggestions": [
            "Suggestion 1",
            "Suggestion 2",
            "Suggestion 3"
        ]
    }}
    
    Ensure all fields are present in the JSON, even if the information is not available in the notes.
    If information for a field is not available, use "Not specified" as the value.
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    llm_response = llm.invoke(messages)
    output_text = llm_response.content

    print(f"Raw OpenAI response: {output_text}")

    try:
        # Clean the response before parsing
        cleaned_output = output_text.strip()
        if cleaned_output.startswith('```json'):
            cleaned_output = cleaned_output[7:-3]  # Remove ```json and ``` 
        structured_data = json.loads(cleaned_output)
        
        # Verify required fields
        required_fields = ['name', 'job', 'last_seen', 'context', 'networking_suggestions']
        for field in required_fields:
            if field not in structured_data:
                structured_data[field] = "Not specified"
        
        # Ensure last_seen is in ISO format
        try:
            structured_data['last_seen'] = datetime.fromisoformat(structured_data['last_seen']).isoformat()
        except ValueError:
            structured_data['last_seen'] = datetime.now().isoformat()
        
        # Ensure context is an array
        if isinstance(structured_data['context'], str):
            structured_data['context'] = [structured_data['context']]
        
        return structured_data
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw output causing error: {output_text}")
    except Exception as e:
        print(f"Unexpected error in process_meeting_notes: {str(e)}")
    
    # If all parsing attempts fail, return a default structure
    return {
        "name": "Unknown",
        "job": "Not specified",
        "last_seen": datetime.now().isoformat(),
        "context": [notes],  # Use raw notes as context in an array
        "networking_suggestions": ["Follow up on the meeting"]
    }