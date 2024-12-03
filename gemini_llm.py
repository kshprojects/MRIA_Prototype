import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv("config/.env")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

genai.configure(api_key=api_key)

def LLM(retrieved_chunks, user_query):
  print("Recieved retrieved chunks to LLM: ", retrieved_chunks)
  generation_config = {
      "temperature": 0.2,
      "top_p": 0.95,
      "top_k": 40,
      "max_output_tokens": 2000,
      "response_mime_type": "text/plain",
  }

  model = genai.GenerativeModel(
      model_name="gemini-1.5-flash",
      generation_config=generation_config,
  )

  chat_session = model.start_chat(history=[])
  conversation_history = []

  # context = "\n".join(retrieved_chunks)
  context = "\n".join(chunk["text"] for chunk in retrieved_chunks)

  prompt = f"""
          You are a highly knowledgeable assistant with expertise in analyzing and synthesizing information. 
          Below are some relevant details retrieved to answer the user's question accurately:

          Relevant Details:
          {context}

          User's Question:
          {user_query}

          Your task:
          - Use the provided relevant details to generate the most accurate and detailed response.
          - Avoid including unrelated or speculative information.
          - Ensure the response is clear, concise, and directly addresses the user's query.
          Provide your response below:
          """
  
#unless until user ask for indetail explanation,Your response should be only max 1-2lines only

  conversation_history.append({"role": "user", "parts": user_query})

  response = chat_session.send_message(prompt)

  print("Response from Gemini:")
  for chunk in response:
      print(chunk.text)
      print("_" * 80)

  conversation_history.append({"role": "model", "parts": response.text})

  print("Conversation History:")
  for message in conversation_history:
      print(f"{message['role'].capitalize()}: {message['parts']}")

  return response.text
  