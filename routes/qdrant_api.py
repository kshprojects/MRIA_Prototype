from flask import Blueprint, request, jsonify
import os
import logging
import torch
from werkzeug.utils import secure_filename
from docs_preprocessing import check_document_type, text_chunking
from openai_clip import embedding_the_chunks
from qdrant import retrieve_from_qdrant, store_chunk_embedding_in_db, create_user_collection, check_collections
from gemini_llm import LLM
from openai_clip import tokenizer, model

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

qdrant_blueprint = Blueprint('qdrant', __name__, url_prefix="/app")

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

device = torch.device("cpu")
model = model.to(device)

def get_model():
    return model

@qdrant_blueprint.route("api/mria/upload_and_process", methods=["POST"])
def upload_and_process():
    try:
        file = request.files.get("file")
        user_collection = request.form.get("user_collection")

        if not file or file.filename == "":
            logger.error("No file selected for uploading")
            return jsonify({"error": "No file selected for uploading"}), 400
        if not user_collection:
            logger.error("User collection is required")
            return jsonify({"error": "User collection is required"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        logger.debug(f"File saved to {file_path}")

        # Ensure the collection exists
        logger.debug(f"Checking collection: {user_collection}")
        collection_status = check_and_create_collection(user_collection)
        if collection_status["status"] != "success":
            logger.error(f"Failed to create or find collection: {user_collection}")
            return jsonify(collection_status), 500

        # Process the file synchronously in the main thread
        logger.debug("Starting document processing")
        result = document_processing(file_path, user_collection, os.path.splitext(filename)[0])

        # Once the processing is done, notify frontend with a success status
        if result["status"] == "success":
            logger.info("File processed successfully")
            return jsonify({"status": "success", "message": "File processed successfully"}), 200
        else:
            logger.error(f"Error processing file: {result['message']}")
            return jsonify({"status": "error", "message": result["message"]}), 500

    except Exception as e:
        logger.error(f"Error in upload_and_process: {e}")
        return jsonify({"error": str(e)}), 500


def check_and_create_collection(user_collection):
    if check_collections(user_collection):
        logger.debug(f"Collection '{user_collection}' exists. No creation needed.")
        return {"status": "success", "message": "Collection ready"}
    
    logger.debug(f"Collection '{user_collection}' does not exist. Creating it...")
    created = create_user_collection(user_collection)
    if not created:
        logger.error(f"Failed to create collection: {user_collection}")
        return {"status": "error", "message": "Failed to create collection"}
    
    logger.debug(f"Collection '{user_collection}' created successfully.")
    return {"status": "success", "message": "Collection created"}


def document_processing(file_path, user_collection, book_name):
    try:
        logger.debug(f"Processing file: {file_path}")
        # Step 1: Check document type and chunk the text
        text = check_document_type(file_path)
        logger.debug("Document type validated. Chunking text...")
        chunks = text_chunking(text)
        logger.debug(f"Text chunked into {len(chunks)} parts.")
        
        # Step 2: Generate embeddings for the chunks
        chunk_embeddings = embedding_the_chunks(chunks)
        logger.debug(f"Generated {len(chunk_embeddings)} embeddings.")

        if not chunk_embeddings:
            logger.error("Embedding failed, no data to store")
            return {"status": "error", "message": "Embedding failed, no data to store"}

        # Step 3: Store embeddings into Qdrant
        logger.debug("Storing embeddings into Qdrant...")
        store_chunk_embedding_in_db(user_collection, chunk_embeddings, chunks, book_name)
        logger.debug("Data successfully stored in Qdrant.")

        return {"status": "success", "message": "File processed and stored in the database"}

    except Exception as e:
        logger.error(f"Error in document_processing: {e}")
        return {"status": "error", "message": str(e)}


@qdrant_blueprint.route("api/mria/query", methods=["POST"])
def query_model():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400

        user_query = data.get("user_query")
        user_collection = data.get("user_collection")

        if not user_query or not user_collection:
            logger.error("Missing required parameters (user_query, user_collection).")
            return jsonify({"error": "Missing required parameters (user_query, user_collection)."}), 400

        # Generate embeddings for the query
        logger.debug("Generating embeddings for the query")
        inputs = tokenizer(user_query, return_tensors="pt", padding=True, truncation=True).to(device)
        with torch.no_grad():
            text_outputs = model(**inputs)
            sentence_embeddings = text_outputs[0][:, 0]

        query_embedding = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1).squeeze(0).cpu().tolist()
        
        # Retrieve relevant chunks from Qdrant
        logger.debug("Retrieving relevant chunks from Qdrant")
        retrieved_chunks = retrieve_from_qdrant(user_collection, query_embedding, top_k=5)

        # Get response from LLM
        logger.debug("Getting response from LLM")
        response = LLM(retrieved_chunks, user_query)
        
        return jsonify({"user_query": user_query, "response": response}), 200

    except Exception as e:
        logger.error(f"Error in query_model: {e}")
        return jsonify({"error": str(e)}), 500
