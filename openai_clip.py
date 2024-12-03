from transformers import AutoModel, AutoTokenizer
from docs_preprocessing import check_document_type, text_chunking
from qdrant import create_user_collection, store_chunk_embedding_in_db
import torch

device = torch.device("cpu")  # Explicitly set to CPU
print("Device: ", device)

model = AutoModel.from_pretrained(
    "BAAI/bge-large-en-v1.5",
    cache_dir="/Users/username/RAG/huggingface_cache",
    device_map="cpu"
).to(device)  # Ensure the model is moved to the correct device

tokenizer = AutoTokenizer.from_pretrained(
    "BAAI/bge-large-en-v1.5",
    cache_dir="/Users/username/RAG/huggingface_cache"
)

def embedding_the_chunks(chunks):
    chunk_embeddings = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True).to(device)  # Ensure input is on the same device
        with torch.no_grad():
            text_outputs = model(**inputs)  
            sentence_embeddings = text_outputs[0][:, 0]
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

        embeddings = sentence_embeddings.squeeze(0).cpu().tolist()  # Flatten
        chunk_embeddings.append(embeddings)
            
    # # Convert embeddings to a Python list or numpy array
    # embeddings = normalized_embeddings.squeeze(0).cpu().tolist()

    print("Embedding size:", len(chunk_embeddings))
    return chunk_embeddings


# model = AutoModel.from_pretrained("openai/clip-vit-base-patch16").to(device)
# processor = AutoImageProcessor.from_pretrained("openai/clip-vit-base-patch16")
# tokenizer = AutoTokenizer.from_pretrained("openai/clip-vit-base-patch16")
            

# print("Process Started")
# pdf = r"E:\\RAG\\uploads\\Foundational_LLM.pdf"
# texts = check_document_type(pdf)
# chunks = text_chunking(texts)
# chunk_embedding = embedding_the_chunks(chunks)
# collection_name = "Collection_Kaif_01"
# create_user_collection(collection_name)
# store_chunk_embedding_in_db(collection_name, chunk_embedding, chunks)

# print("Process Finished")

