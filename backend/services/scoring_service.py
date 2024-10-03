import os
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0.2, model_name="gpt-4o-mini", openai_api_key=openai_api_key)

def calculate_score(invoice_data):
    system_prompt = "You are a risk assessment AI for invoice financing. Provide a risk score between 0 and 1, where 0 is lowest risk and 1 is highest risk."
    user_prompt = f"""
    Given the following invoice data, calculate a risk score:
    
    Invoice Number: {invoice_data['invoice_number']}
    Amount: {invoice_data['amount']}
    Client: {invoice_data['client']}
    Due Date: {invoice_data['due_date']}
    Description: {invoice_data['description']}
    
    Respond with only a number between 0 and 1, representing the risk score.
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    llm_response = llm.invoke(messages)
    score = float(llm_response.content.strip())
    return score