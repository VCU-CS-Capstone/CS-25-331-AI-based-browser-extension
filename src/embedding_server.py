from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import chromadb
import re

app = Flask(__name__)

# Initialize embedding model
model = SentenceTransformer("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")

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
        url = data.get("url", "unknown_url")
        project = data.get("project", "default")

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Chunk text
        chunks = chunk_text(text)
        print(f"[{project}] Chunked {len(chunks)} parts from {url}")

        # Generate and store embeddings
        embeddings = model.encode(chunks).tolist()
        for i, embedding in enumerate(embeddings):
            unique_id = f"{project}_{url}_chunk_{i}"
            collection.add(
                ids=[unique_id],
                embeddings=[embedding],
                metadatas=[{
                    "text": chunks[i],
                    "url": url,
                    "project": project
                }]
            )

        return jsonify({"chunks": chunks, "message": "Embeddings stored successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/query", methods=["POST"])
def query_embeddings():
    try:
        data = request.json
        question = data.get("question", "")
        project = data.get("project", "default")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        query_embedding = model.encode([question])[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={"project": project}
        )

        matches = []
        seen_urls = set()
        for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
            similarity = round(1 - distance, 4)
            if similarity <= 0:
                continue  # Skip weak or dissimilar results

            url = metadata["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                matches.append({
                    "url": url,
                    "text": metadata["text"],
                    "score": similarity
                })

            if len(matches) >= 3:
                break


        return jsonify({"matches": matches}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)