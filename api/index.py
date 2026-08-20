import asyncio
import io
from flask import Flask, render_template_string, request, send_file, Response
import edge_tts

app = Flask(__name__)

VOICES = {
    "🥰 Kuchu Puchu (Cute Baby)": "hi-IN-SwaraNeural",
    "👧 Swara (Female)": "hi-IN-SwaraNeural",
    "👧 Ananya (Soft Female)": "hi-IN-SwaraNeural",
    "👧 Kavya (Deep Female)": "en-IN-NeerjaNeural",
    "👦 Madhur (Male)": "hi-IN-MadhurNeural",
    "👦 Rohan (Young Male)": "hi-IN-MadhurNeural",
    "👦 Vikram (Deep Male)": "hi-IN-MadhurNeural",
}

EMOTIONS = {
    "🤖 Auto Detect Tone": "auto",
    "😊 Normal / Happy": {"pitch": "+0Hz", "rate": "+0%", "volume": "+0%"},
    "🎉 Excited / Energetic": {"pitch": "+15Hz", "rate": "+20%", "volume": "+20%"},
    "😢 Sad / Emotional": {"pitch": "-10Hz", "rate": "-20%", "volume": "-15%"},
    "😠 Angry / Aggressive": {"pitch": "-5Hz", "rate": "+15%", "volume": "+30%"},
    "😱 Scared / Question": {"pitch": "+20Hz", "rate": "+15%", "volume": "+0%"},
    "🤫 Whisper / Soft": {"pitch": "+5Hz", "rate": "-15%", "volume": "-30%"}
}

def detect_auto_tone(text):
    text_lower = text.lower()
    if any(word in text_lower for word in ['gussa', 'angry', 'pagal', 'maro', 'chup']):
        return EMOTIONS["😠 Angry / Aggressive"]
    elif any(word in text_lower for word in ['sad', 'dukh', 'rona', 'akela', 'sorry', 'dard']):
        return EMOTIONS["😢 Sad / Emotional"]
    elif any(word in text_lower for word in ['kya', 'kyu', 'kaise', 'kab', '?']):
        return EMOTIONS["😱 Scared / Question"]
    elif '!' in text or any(word in text_lower for word in ['wow', 'maza', 'great', 'khush', 'yay']):
        return EMOTIONS["🎉 Excited / Energetic"]
    else:
        return EMOTIONS["😊 Normal / Happy"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vercel TTS Studio</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 20px; background: #f0f2f5; }
        .card { background: white; padding: 25px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 92%; max-width: 550px; }
        h2 { color: #333; margin-bottom: 20px; }
        textarea { width: 95%; height: 110px; padding: 10px; border-radius: 8px; border: 1px solid #ccc; font-size: 15px; }
        label { display: block; text-align: left; margin-top: 12px; font-weight: bold; color: #444; }
        select { width: 98%; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #ccc; font-size: 15px; background: #fff; }
        button { background: #28a745; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold; margin-top: 20px; }
        audio { margin-top: 20px; width: 100%; }
        .download-btn { display: block; margin-top: 15px; background: #007bff; color: white; padding: 11px; text-decoration: none; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚀 Vercel Auto-Tone Voice Studio</h2>
        <form method="POST" action="/generate">
            <textarea name="text" placeholder="Apna text yahan likhein..." required></textarea>
            
            <label for="voice">Voice Select Karein:</label>
            <select name="voice" id="voice">
                {% for name in voices.keys() %}
                    <option value="{{ name }}">{{ name }}</option>
                {% endfor %}
            </select>

            <label for="emotion">Tone / Emotion Mode:</label>
            <select name="emotion" id="emotion">
                {% for emo in emotions.keys() %}
                    <option value="{{ emo }}">{{ emo }}</option>
                {% endfor %}
            </select>

            <button type="submit">Audio Generate & Play Karein</button>
        </form>
    </div>
</body>
</html>
"""

async def generate_audio_stream(text, voice_id, pitch, rate, volume):
    communicate = edge_tts.Communicate(text=text, voice=voice_id, pitch=pitch, rate=rate, volume=volume)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, voices=VOICES, emotions=EMOTIONS)

@app.route('/generate', methods=['POST'])
def generate():
    text = request.form.get('text', '')
    selected_voice = request.form.get('voice')
    selected_emotion = request.form.get('emotion')

    if not text.strip():
        return "Text required", 400

    voice_id = VOICES.get(selected_voice, "hi-IN-SwaraNeural")

    if selected_emotion == "🤖 Auto Detect Tone":
        emo_config = detect_auto_tone(text)
    else:
        emo_config = EMOTIONS.get(selected_emotion, EMOTIONS["😊 Normal / Happy"])

    if selected_voice == "🥰 Kuchu Puchu (Cute Baby)":
        pitch = "+30Hz"
        rate = "+15%"
        volume = emo_config["volume"]
    else:
        pitch = emo_config["pitch"]
        rate = emo_config["rate"]
        volume = emo_config["volume"]

    # Stream direct to response (No file saving)
    audio_bytes = asyncio.run(generate_audio_stream(text, voice_id, pitch, rate, volume))
    
    return Response(
        audio_bytes,
        mimetype="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=voice.mp3"}
    )

# Vercel entry point
app = app
