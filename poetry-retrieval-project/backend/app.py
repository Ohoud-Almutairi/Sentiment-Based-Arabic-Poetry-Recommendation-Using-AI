# شِعرُك Backend API
# Flask + AraBERT + CSV Poetry Database

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import pandas as pd
import json
import os
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend


# Configuration
# ========================================
MODEL_PATH = '../models/arabert-emotion-final'
POETRY_CSV_PATH = '../data/poems_dataset2.csv'  


# Load Model
# ========================================
print("\n🚀 Loading AraBERT model...")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model.to(device)
model.eval()

# Check if model has proper labels
id2label = model.config.id2label

# If model has generic labels (LABEL_0, LABEL_1, LABEL_2), map them manually
if 'LABEL_0' in str(id2label.values()):
    print("⚠️  Model has generic labels, applying manual mapping...")
    
    # Correct mapping 
    id2label = {
        0: 'joy',
        1: 'love',
        2: 'sad'
    }
    
    # Update model config
    model.config.id2label = id2label
    model.config.label2id = {'joy': 0, 'love': 1, 'sad': 2}
    
    print("✓ Labels mapped: LABEL_0→joy, LABEL_1→love, LABEL_2→sad")

print(f"✓ Model loaded on {device}")
print(f"✓ Emotions: {list(id2label.values())}")



# Load Poetry Database
# ========================================
print("\n📖 Loading poetry database...")

poetry_df = pd.read_csv(POETRY_CSV_PATH, encoding='utf-8')
print(f"✓ Loaded {len(poetry_df)} poems")

# specific columns
text_col = 'poem'
emotion_col = 'emotion'

# Verify columns exist
if text_col not in poetry_df.columns or emotion_col not in poetry_df.columns:
    print(f"❌ Error: Required columns not found")
    print(f"Expected: ['poem', 'emotion']")
    print(f"Found: {poetry_df.columns.tolist()}")
    exit(1)

print(f"✓ Using columns: poem, emotion")

# Clean data
poetry_df = poetry_df.dropna(subset=[text_col, emotion_col])

# Normalize emotions
emotion_map = {
    'joy': 'joy', 'فرح': 'joy', 'سعادة': 'joy', 'happiness': 'joy', 'happy': 'joy',
    'love': 'love', 'حب': 'love',
    'sad': 'sad', 'حزن': 'sad', 'sadness': 'sad'
}

poetry_df[emotion_col] = poetry_df[emotion_col].str.lower().str.strip()
poetry_df['emotion_normalized'] = poetry_df[emotion_col].map(emotion_map)
poetry_df = poetry_df.dropna(subset=['emotion_normalized'])

# Organize by emotion
poetry_database = {}
for emotion in ['joy', 'love', 'sad']:
    poems = poetry_df[poetry_df['emotion_normalized'] == emotion]
    poetry_database[emotion] = [{'text': str(row[text_col])} for _, row in poems.iterrows()]
    print(f"  - {emotion}: {len(poetry_database[emotion])} poems")

print(f"✓ Total: {sum(len(v) for v in poetry_database.values())} poems\n")


# Helper Functions
# ========================================
def detect_emotion(text):
    """Detect emotion from text"""
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    predicted_class = torch.argmax(probs, dim=-1).item()
    
    return {
        'emotion': id2label[predicted_class],
        'confidence': round(probs[0][predicted_class].item(), 4),
        'all_probabilities': {id2label[i]: round(probs[0][i].item(), 4) for i in range(len(id2label))}
    }

def get_random_poem(emotion):
    """Get one random poem for emotion"""
    poems = poetry_database.get(emotion, [])
    return random.choice(poems) if poems else None


# API Routes
# ========================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'شِعرُك Poetry Retrieval API',
        'status': 'running',
        'emotions': list(id2label.values()),
        'total_poems': sum(len(v) for v in poetry_database.values())
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'device': str(device),
        'emotions': list(id2label.values())
    })

@app.route('/get-poetry', methods=['POST'])
def get_poetry():
    """Main endpoint: detect emotion and return poem"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Detect emotion
        emotion_result = detect_emotion(text)
        
        # Get one poem
        poem = get_random_poem(emotion_result['emotion'])
        
        return jsonify({
            'text': text,
            'emotion': emotion_result['emotion'],
            'confidence': emotion_result['confidence'],
            'all_probabilities': emotion_result['all_probabilities'],
            'poetry': [poem] if poem else [],
            'poetry_count': 1 if poem else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Run
# ========================================

if __name__ == '__main__':
    print("="*60)
    print("🚀 Starting شِعرُك API on http://localhost:5000")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)