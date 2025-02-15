# Run python embedding_server.py then go to http://127.0.0.1:8080

from flask import Flask, request, jsonify
from transformers import pipeline

# Initialize the Flask app
app = Flask(__name__)

# Load the embedding model
print("Loading the model...")
embedder = pipeline("feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2")
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
print("Model loaded successfully!")

def chunk_text_by_tokens(text, max_tokens=256):
    """Splits text into chunks based on token count."""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = [tokens[i : i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    return [tokenizer.decode(chunk) for chunk in chunks]

@app.route("/")
def home():
    return "Embedding server is running!"

@app.route("/generate_embeddings", methods=["POST"])
def generate_embeddings():
    try:
        # Get the sentence from the POST request
        data = request.json
        sentence = data.get("sentence", "")
        if not sentence:
            return jsonify({"error": "No sentence provided"}), 400

        # Split text into chunks
        chunks = chunk_text_by_tokens(text, max_tokens=256)

        # Generate embeddings
        print(f"Generating embeddings for: {sentence}")
        embeddings = [embedder(chunk)[0] for chunk in chunks]

        # Convert embeddings to plain arrays
        plain_embeddings = [
            emb[0] if isinstance(emb, list) and len(emb) > 0 else emb
            for emb in embeddings
        ]

        return jsonify({"embeddings": plain_embeddings, "chunks": chunks})
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
