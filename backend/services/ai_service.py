import os
from langchain_openai import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage
)
import json

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0.5, model_name="gpt-4", openai_api_key=openai_api_key)

def process_ai_query(query: str, contacts: list):
    contacts_json = json.dumps(contacts)
    system_prompt = "You are a helpful assistant that answers questions about a user's network based on their contacts data."
    user_prompt = f"""
    Given the following contacts data and user query, provide a helpful answer:
    
    Contacts: {contacts_json}
    User Query: {query}
    
    Please provide a concise and relevant answer based on the information in the contacts data.

    # Mandatory:

    - Use the same language as the provided input.
    - Use minimal formatting (e.g., bold or italics if necessary), but keep it simple and professional.
    - Use a concise and professional tone, avoiding unnecessary details or a narrative style.
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    llm_response = llm.invoke(messages)
    return llm_response.content
