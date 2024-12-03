from datetime import datetime
from flask import request, jsonify, Blueprint
import requests
import base64
from config.db_config import firestore, queries_collection, responses_collection, conversations_collection
import whisper
import sounddevice as sd
import numpy as np
import tempfile
import os
from scipy.io.wavfile import write
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv(dotenv_path="config/.env")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

# Blueprint definition for queries
queries = Blueprint('queries', __name__, url_prefix="/app")

# Function to record and transcribe audio
def transcribe_audio(duration=10, fs=44100):
    try:
        # Record the audio
        print("Recording... Please speak now.")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()  # Wait until recording is finished
        
        # Save the recorded audio temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmpfile:
            write(tmpfile.name, fs, audio)  # Save as WAV file
            
            # Load Whisper model
            model = whisper.load_model("base")
            
            # Transcribe audio
            print("Transcribing audio...")
            result = model.transcribe(tmpfile.name)
            
            # Clean up the temporary file
            os.remove(tmpfile.name)
            
            # Return the transcription text
            return result['text']
    except Exception as e:
        raise Exception(f"Error in transcribing audio: {str(e)}")

# Route to handle the "Speak" button and transcription
@queries.route('api/conversations/transcribe_audio', methods=['POST'])
def transcribe_audio_route():
    try:
        # You can adjust the duration of the recording if needed
        transcription = transcribe_audio(duration=10)  # Adjust the duration as needed
        return jsonify({"transcription": transcription}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


'''@queries.route('api/conversations/<conversation_id>/add_query_response', methods=["POST"])
def add_query_response(conversation_id):
    try:
        # Retrieve the conversation document
        conversation_ref = conversations_collection.document(conversation_id)
        conversation = conversation_ref.get()

        if not conversation.exists:
            return jsonify({"error": "Conversation not found"}), 404

        # Parse the incoming request data
        if request.is_json:
            data = request.get_json()  # If JSON payload
        else:
            data = request.form  # If form data

        query_text = data.get('query') if data else None
        image = request.files.get('image')  # Image should be uploaded as a form-data file

        # Create the query object
        query = {
            "conversation_id": conversation_id,
            "created_at": datetime.utcnow()  # Fixed time zone issue
        }

        if query_text:
            query["query_text"] = query_text

        if image:
            image_data = base64.b64encode(image.read()).decode('utf-8')
            query["query_image"] = image_data

        if not query_text and not image:
            return jsonify({"error": "Either query text or image is required"}), 400

        # Add the new query to Firestore
        query_ref = queries_collection.add(query)  # add() returns a tuple
        print("query_ref:", query_ref)  # Debugging line to print the tuple

        # Access the DocumentReference (first element of the tuple)
        query_doc_ref = query_ref[1]  # Get the DocumentReference from the tuple
        query_id = query_doc_ref.id  # Use the DocumentReference to get the document ID
        print("query_id:", query_id)  # Debugging line to print the query_id

        # Update the conversation document to include the new query
        conversation_ref.update({
            "queries": firestore.ArrayUnion([query_id])
        })

        # Now, directly handle adding the response after the query is added
        response_text = None
        response_id = None
        if query_text:
            response_text = ollama_model.get_ollama_response(query_text)
            
            # Add the response as a new response document
            response = {
                "conversation_id": conversation_id,
                "query_id": query_id,
                "response_text": response_text,
                "created_at": datetime.utcnow()
            }
            response_ref = responses_collection.add(response)  # add() returns a tuple
            print("response_ref:", response_ref)  # Debugging line to print the tuple

            # Access the DocumentReference (first element of the tuple)
            response_doc_ref = response_ref[1]  # Get the DocumentReference from the tuple
            response_id = response_doc_ref.id  # Use the DocumentReference to get the document ID
            print("response_id:", response_id)  # Debugging line to print the response_id

            # Update the query document with the response ID
            query_doc_ref.update({
                "response_id": response_id,
                "response_text": response_text
            })

            # Update the conversation document to include the new response ID
            conversation_ref.update({
                "responses": firestore.ArrayUnion([response_id])
            })

        return jsonify({
            "query_id": query_id, 
            "response_id": response_id, 
            "response_text": response_text,
            "message": "Query added and response generated successfully"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
'''

@queries.route('api/conversations/<conversation_id>/add_query_response', methods=["POST"])
def add_query_response(conversation_id):
    try:
        # Retrieve the conversation document
        conversation_ref = conversations_collection.document(conversation_id)
        conversation = conversation_ref.get()

        if not conversation.exists:
            return jsonify({"error": "Conversation not found"}), 404

        user_id = conversation.to_dict().get("user_id")
        if not user_id:
            return jsonify({"error": "User ID not found in the conversation"}), 400

        # Proceed with logic
        collection_name = f"Collection{user_id}"

        # Parse the incoming request data
        if request.is_json:
            data = request.get_json()  # If JSON payload
        else:
            data = request.form  # If form data

        query_text = data.get('query') if data else None
        image = request.files.get('image')  # Image should be uploaded as a form-data file

        # Create the query object
        query = {
            "conversation_id": conversation_id,
            "created_at": datetime.utcnow()  # Fixed time zone issue
        }

        if query_text:
            query["query_text"] = query_text

        if image:
            image_data = base64.b64encode(image.read()).decode('utf-8')
            query["query_image"] = image_data

        if not query_text and not image:
            return jsonify({"error": "Either query text or image is required"}), 400

        # Add the new query to Firestore
        query_ref = queries_collection.add(query)  # add() returns a tuple
        query_doc_ref = query_ref[1]  # Get the DocumentReference from the tuple
        query_id = query_doc_ref.id

        # Update the conversation document to include the new query
        conversation_ref.update({
            "queries": firestore.ArrayUnion([query_id])
        })

        # Fetch response from Qdrant API
        response = None
        response_id = None
        if query_text:
            qdrant_api_url = "http://127.0.0.1:5000/app/api/mria/query" # Adjust URL if needed
            qdrant_payload = {
                "user_query": query_text,
                "user_collection": collection_name  # Use conversation_id as the collection name
            }

            headers = {
                    "Authorization": f"Bearer {qdrant_api_key}"
                }
            qdrant_response = requests.post(qdrant_api_url, json=qdrant_payload,headers=headers)

            if qdrant_response.status_code == 200:
                qdrant_data = qdrant_response.json()
                response = qdrant_data.get("response")

                # Add the response as a new response document
                response_doc = {
                    "conversation_id": conversation_id,
                    "query_id": query_id,
                    "response_text": response,
                    "created_at": datetime.utcnow()
                }

                response_ref = responses_collection.add(response_doc)  # Add response to Firestore
                response_doc_ref = response_ref[1]
                response_id = response_doc_ref.id

                # Update the query document with the response ID
                query_doc_ref.update({
                    "response_id": response_id,
                    "response_text": response
                })

                # Update the conversation document to include the new response ID
                conversation_ref.update({
                    "responses": firestore.ArrayUnion([response_id])
                })
            else:
                return jsonify({"error": "Failed to fetch response from Qdrant API"}), qdrant_response.status_code

        return jsonify({
            "query_id": query_id,
            "response_id": response_id,
            "response_text": response,
            "message": "Query added and response generated successfully"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get all query IDs for a conversation
@queries.route('api/conversations/get_query_ids/<conversation_id>', methods=['GET'])
def get_query_ids(conversation_id):
    try:
        conversation_ref = conversations_collection.document(conversation_id)
        conversation = conversation_ref.get()

        if not conversation.exists:
            return jsonify({"error": "Conversation not found"}), 404

        query_ids = conversation.to_dict().get('queries', [])
        return jsonify({
            "conversation_id": conversation_id,
            "query_ids": query_ids
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to retrieve all queries and responses for a conversation
@queries.route('api/conversations/retrieve/<conversation_id>', methods=["GET"])
def retrieve(conversation_id):
    try:
        conversation_ref = conversations_collection.document(conversation_id)
        conversation = conversation_ref.get()

        if not conversation.exists:
            return jsonify({"error": "Conversation not found"}), 404

        query_ids = conversation.to_dict().get('queries', [])
        queries_list = []
        
        for query_id in query_ids:
            query_doc = queries_collection.document(query_id).get()
            if query_doc.exists:
                query_data = query_doc.to_dict()
                response_doc = responses_collection.document(query_data.get("response_id", "")).get() if query_data.get("response_id") else None
                query_data["response"] = {
                    "response_id": response_doc.id if response_doc and response_doc.exists else None,
                    "response_text": response_doc.to_dict().get("response_text") if response_doc and response_doc.exists else None,
                    "created_at": response_doc.to_dict().get("created_at") if response_doc and response_doc.exists else None
                } if response_doc else None
                query_data["query_id"] = query_id
                queries_list.append(query_data)

        return jsonify({
            "conversation_id": conversation_id,
            "queries": queries_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
