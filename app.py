from flask import Flask, request, render_template, jsonify
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import pyttsx3
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

app = Flask(__name__)

# ===============================
# Global Variables
# ===============================
last_caption = None
last_translated_caption = None
last_language = "en"

# ===============================
# Load BLIP Model
# ===============================
processor = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-large"
)
model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-large"
)

# ===============================
# Safe English Text-to-Speech
# ===============================
def speak_english(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("TTS Error:", e)
        raise e

# ===============================
# Routes
# ===============================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/caption", methods=["POST"])
def caption_image():
    global last_caption, last_translated_caption, last_language

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    language = request.form.get("language", "en")
    last_language = language

    image_file = request.files["image"]
    raw_image = Image.open(image_file).convert("RGB")

    prompt = "A photography of"
    inputs = processor(raw_image, prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            num_beams=5,
            num_return_sequences=3,
            max_length=50,
            output_scores=True,
            return_dict_in_generate=True
        )

    captions = [
        processor.decode(out, skip_special_tokens=True)
        for out in outputs["sequences"]
    ]

    # Calculate accuracy scores (confidence)
    accuracy_scores = []
    if "sequences_scores" in outputs:
        import numpy as np
        scores = outputs["sequences_scores"].cpu().numpy()
        # Convert log probabilities to probabilities using exponential
        accuracy_scores = [float(np.exp(score) * 100) for score in scores]

    last_caption = captions[0]

    # ===== Dynamic Translation =====
    if language != "en":
        try:
            last_translated_caption = GoogleTranslator(
                source='auto', target=language
            ).translate(last_caption)
        except Exception as e:
            print("Translation Error:", e)
            last_translated_caption = "Translation not available"
    else:
        last_translated_caption = None

    return jsonify({
        "best_caption": last_caption,
        "best_caption_accuracy": accuracy_scores[0] if accuracy_scores else None,
        "translated_caption": last_translated_caption,
        "language": language,
        "all_captions": captions,
        "all_accuracy_scores": accuracy_scores
    })


# ===============================
# Speak English (Offline)
# ===============================
@app.route("/speak", methods=["POST"])
def speak():
    if not last_caption:
        return jsonify({"error": "No caption available"}), 400

    try:
        speak_english(last_caption)
        return jsonify({"status": "english spoken"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===============================
# Speak Selected Language (gTTS)
# ===============================
@app.route("/speak_translated", methods=["POST"])
def speak_translated():
    global last_translated_caption, last_language

    if not last_translated_caption:
        return jsonify({"error": "No translated caption available"}), 400

    try:
        # Ensure static folder exists
        if not os.path.exists("static"):
            os.makedirs("static")

        audio_path = os.path.join("static", "output.mp3")

        tts = gTTS(
            text=last_translated_caption,
            lang=last_language
        )

        tts.save(audio_path)

        return jsonify({
            "audio_url": "/static/output.mp3"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===============================
# Run App
# ===============================
if __name__ == "__main__":
    app.run(debug=True, threaded=True)
