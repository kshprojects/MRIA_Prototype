from flask import jsonify, Blueprint, request
from datetime import datetime
from config.db_config import db
from config.db_config import firestore,queries_collection,users_collection,responses_collection,conversations_collection

# Define blueprint for conversation routes
conversation_blueprint = Blueprint('conversation', __name__, url_prefix='/app')

# Route to create a new conversation for a user
@conversation_blueprint.route('/api/create_conversation/<user_id>', methods=['POST'])
def create_conversation(user_id):
    try:
        # Check if user exists in the users collection
        user_ref = users_collection.document(user_id)
        if not user_ref.get().exists:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Create a new conversation document
        new_conversation = {
            "user_id": user_id,
            "queries": [],
            "responses": [],
            "created_at": datetime.utcnow()
        }

        # Add the conversation to Firestore and get its document ID
        conversation_ref = conversations_collection.add(new_conversation)
        conversation_id = conversation_ref[1].id

        # Update the user's document by adding the new conversation ID
        user_ref.update({
            "conversations": firestore.ArrayUnion([conversation_id])
        })

        return jsonify({"status": "success", "conversation_id": conversation_id}), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Route to get a specific conversation using its ID
@conversation_blueprint.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    try:
        # Retrieve the conversation document
        conversation_ref = conversations_collection.document(conversation_id)
        conversation = conversation_ref.get()

        if not conversation.exists:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404

        conversation_data = conversation.to_dict()

        return jsonify({
            "status": "success",
            "conversation_id": conversation_id,
            "user_id": conversation_data["user_id"],
            "queries": conversation_data['queries'],
            "responses": conversation_data['responses'],
            "created_at": conversation_data["created_at"]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@conversation_blueprint.route('/api/conversations/user/<user_id>', methods=['GET'])
def get_user_conversations(user_id):
    try:
        # Check if the user exists
        user_ref = users_collection.document(user_id)
        user = user_ref.get()
        if not user.exists:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Retrieve conversation IDs from the user's document
        user_data = user.to_dict()
        conversation_ids = user_data.get('conversations', [])
        conversations = []

        for conversation_id in conversation_ids:
            conv_ref = conversations_collection.document(conversation_id)
            conv = conv_ref.get()
            if conv.exists:
                conversation_data = conv.to_dict()

                # Fetch full query objects
                query_objects = []
                for query_id in conversation_data.get('queries', []):
                    query_ref = queries_collection.document(query_id)
                    query_doc = query_ref.get()
                    if query_doc.exists:
                        query_objects.append({
                            "query_id": query_id,
                            **query_doc.to_dict()
                        })

                conversations.append({
                    "conversation_id": conversation_id,
                    "queries": query_objects,  # Include full query objects
                    "responses": conversation_data.get('responses', []),
                    "created_at": conversation_data["created_at"]
                })

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "conversations": conversations
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


