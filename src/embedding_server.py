# Run python embedding_server.py then go to http://127.0.0.1:8080

from flask import Flask, request, jsonify
from transformers import pipeline

# Initialize the Flask app
app = Flask(__name__)

# Load the embedding model
print("Loading the model...")
embedder = pipeline("feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2")
print("Model loaded successfully!")

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

        # Generate embeddings
        print(f"Generating embeddings for: {sentence}")
        embeddings = embedder(sentence)

        # Convert embeddings to plain arrays
        plain_embeddings = (
            embeddings[0] if isinstance(embeddings, list) and len(embeddings) > 0 else embeddings
        )

        return jsonify({"embeddings": plain_embeddings})
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
