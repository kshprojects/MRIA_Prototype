from flask import jsonify, Blueprint, request
from config.db_config import firestore,queries_collection,users_collection,responses_collection,conversations_collection
from datetime import datetime
from config.db_config import db
from config.db_config import firestore

# Define the blueprint for response routes
responses = Blueprint('responses', __name__, url_prefix='/app')

# Route to add a response to a query within a conversation
@responses.route('api/conversations/<conversation_id>/add_response', methods=['POST'])
def add_response(conversation_id):
    try:
        # Retrieve the conversation document
        conversation_ref = conversations_collection.document(conversation_id)
        conversation = conversation_ref.get()
        if not conversation.exists:
            return jsonify({"error": "Conversation not found"}), 404

        # Retrieve response data from request
        data = request.get_json()
        response_text = data.get('response')
        query_id = data.get('query_id')

        if not response_text or not query_id:
            return jsonify({"error": "Both response text and query ID are required"}), 400

        # Check if the query exists
        query_ref = queries_collection.document(query_id)
        query = query_ref.get()
        if not query.exists or query.to_dict().get("conversation_id") != conversation_id:
            return jsonify({"error": "Query not found"}), 404

        # Create a new response document
        response_data = {
            "conversation_id": conversation_id,
            "query_id": query_id,
            "response_text": response_text,
            "created_at": datetime.utcnow()
        }
        response_ref = responses_collection.add(response_data)
        response_id = response_ref[1].id

        # Update the query document with the new response ID
        query_ref.update({"response_id": response_id})

        # Update the conversation document to add the new response ID
        conversation_ref.update({"responses": firestore.ArrayUnion([response_id])})

        return jsonify({"response_id": response_id, "message": "Response added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Route to get all responses for a specific conversation
@responses.route('/conversations/<conversation_id>/responses', methods=['GET'])
def get_responses(conversation_id):
    try:
        # Retrieve the conversation document
        conversation_ref = conversations_collection.document(conversation_id)
        conversation = conversation_ref.get()

        if not conversation.exists:
            return jsonify({"error": "Conversation not found"}), 404

        response_ids = conversation.to_dict().get('responses', [])

        # Retrieve all response documents associated with the conversation
        response_list = []
        for response_id in response_ids:
            response = responses_collection.document(response_id).get()
            if response.exists:
                response_data = response.to_dict()
                response_data["response_id"] = response_id
                response_list.append(response_data)

        return jsonify({
            "conversation_id": conversation_id,
            "responses": response_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to get a specific response using its ID
@responses.route('/responses/<response_id>', methods=['GET'])
def get_response(response_id):
    try:
        response_ref = responses_collection.document(response_id)
        response = response_ref.get()

        if not response.exists:
            return jsonify({"error": "Response not found"}), 404

        response_data = response.to_dict()
        response_data["response_id"] = response_id

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
