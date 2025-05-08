import requests
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = 'llama-3.3-70b-versatile'

# function to call groq llm with context and question
def query_llm(context, user_question):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # prompt structure
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant that uses knowledge graph context to answer questions."},
        {"role": "user", "content": f"Context: {context}\nQuestion: {user_question}"}
    ]

    # payload: actual data that is being sent to the server
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7
    }

    # send post request to groq api
    response = requests.post(url, headers=headers, json=payload)

    # extract generated response
    return response.json()["choices"][0]["message"]["content"]