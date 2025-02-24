from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import chromadb
import re

app = Flask(__name__)

# Initialize embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="embeddings")

def chunk_text(text, max_length=500):
    """Splits text into chunks of complete sentences under max_length."""
    sentences = re.split(r'(?<=[.!?]) +', text)  # Split by sentence boundaries
    chunks, current_chunk = [], ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

@app.route("/generate_embeddings", methods=["POST"])
def generate_embeddings():
    try:
        data = request.json
        text = data.get("text", "")
        url = data.get("url", "unknown_url")  # Default value if no URL provided

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Chunk text before embedding
        chunks = chunk_text(text)
        print(f"Chunked into {len(chunks)} parts from {url}.")

        # Generate embeddings
        embeddings = model.encode(chunks).tolist()

        # Store embeddings in ChromaDB
        for i, embedding in enumerate(embeddings):
            unique_id = f"{url}_chunk_{i}"  # Ensures uniqueness based on URL
            collection.add(
                ids=[unique_id],
                embeddings=[embedding],
                metadatas=[{"text": chunks[i], "url": url}]
            )

        return jsonify({"chunks": chunks, "message": "Embeddings stored successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
