from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import time,uuid

# Initialize Qdrant client
client = QdrantClient(url="http://localhost:6333")

# Check the list of existing collections
collection_lst = client.get_collections()
print(f"Total collections: {len(collection_lst.collections)}")
for i in range(len(collection_lst.collections)):
    print(collection_lst.collections[i].name)

def check_collections(user_collection):
    """Check if the collection already exists."""
    try:
        collection_list = [collection.name for collection in client.get_collections().collections]
        if user_collection in collection_list:
            print(f"Collection '{user_collection}' already exists. Skipping creation.")
            return True  # Collection exists, no need to create
        return False  # Collection doesn't exist
    except Exception as e:
        print(f"Error checking collections: {e}")
        return False

def create_user_collection(user_id):
    """Create a new collection if it doesn't already exist."""
    collection_name = user_id
    try:
        if not check_collections(collection_name):
            # Create the collection if it doesn't exist
            print(f"Creating collection: {collection_name}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.DOT, on_disk=True)
            )
            print(f"Collection {collection_name} successfully created.")
            return True  # Return true only when creation is successful
        else:
            print(f"Collection {collection_name} already exists.")
            return False  # Don't create if already exists
    except Exception as e:
        print(f"Error while creating collection {collection_name}: {e}")
        return False  # Return false if there's an error during creation

def store_chunk_embedding_in_db(collection_name, chunk_embeddings, chunk_texts, book_name, batch_size=1000):
    """
    Store chunk embeddings in Qdrant in batches to avoid timeouts and handle large data efficiently.
    """
    try:
        for i in range(0, len(chunk_embeddings), batch_size):
            batch_embeddings = chunk_embeddings[i:i + batch_size]
            batch_texts = chunk_texts[i:i + batch_size]
            
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),  # Ensure unique ID for each point
                    vector=embedding,
                    payload={"text": batch_texts[j], "book_name": book_name}  # Add book_name to payload
                )
                for j, embedding in enumerate(batch_embeddings)
            ]
            
            # Upsert the batch of points into Qdrant
            start_time = time.time()    
            client.upsert(collection_name=collection_name, points=points)
            elapsed_time = time.time() - start_time
            print(f"Stored batch {i//batch_size + 1}: {len(batch_embeddings)} chunks in {elapsed_time:.2f} seconds.")
            
        print(f"Successfully stored {len(chunk_embeddings)} chunks in collection {collection_name}.")
    except Exception as e:
        print(f"Error while storing chunk embeddings: {e}")
        raise  # Re-raise to propagate the error if needed

def retrieve_from_qdrant(collection_name, query_embedding, top_k=20):
    """
    Retrieve the top-k relevant chunks from Qdrant using the query embedding.
    """
    try:
        # Search for the top_k closest matches in the Qdrant collection
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )
        
        retrieved_chunks = [
            {"text": result.payload["text"], "score": result.score} for result in search_results
        ]
        
        print(f"Retrieved {len(retrieved_chunks)} chunks from Qdrant.")
        return retrieved_chunks
    except Exception as e:
        print(f"Error while retrieving from Qdrant: {e}")
        return []  # Return empty list if there was an error
