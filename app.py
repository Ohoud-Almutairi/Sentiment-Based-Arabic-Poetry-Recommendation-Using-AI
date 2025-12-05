from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({"message": "Backend is working!"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    user_text = data.get("text", "")

    # Placeholder (يمكن تعدلينه لاحقاً)
    predicted_emotion = "happy"
    poem = "ألا ليت الشباب يعود يوماً"

    return jsonify({
        "input": user_text,
        "emotion": predicted_emotion,
        "recommended_poem": poem
    })

if __name__ == "__main__":
    app.run(debug=True)
