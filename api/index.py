import asyncio
import io
import time
from flask import Flask, render_template_string, request, Response
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
    <title>Voice Studio - AI Text to Speech</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- Popunder Ad -->
    <script src="https://pl30942347.effectivecpmnetwork.com/35/31/e1/3531e135d4c8417e0889f1683b5d7566.js"></script>

    <!-- Social Bar Ad -->
    <script src="https://pl30942051.effectivecpmnetwork.com/94/6f/f2/946ff2b19f8122ef113db191ed670ade.js"></script>

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }

        body {
            background: radial-gradient(circle at 15% 0%, rgba(99,102,241,0.12), transparent 30%),
                        radial-gradient(circle at 90% 10%, rgba(16,185,129,0.08), transparent 25%),
                        #f5f7fb;
            color: #1f2937;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px 15px;
        }

        .container {
            width: 100%;
            max-width: 760px;
        }

        .ad-banner-top {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
            overflow: hidden;
        }

        .brand-wrapper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }

        .brand-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            width: 46px;
            height: 46px;
            border-radius: 14px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            font-size: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 20px rgba(99,102,241,0.25);
        }

        .brand-title {
            font-size: 20px;
            font-weight: 800;
            color: #111827;
            line-height: 1.1;
        }

        .brand-subtitle {
            font-size: 12px;
            color: #6b7280;
            margin-top: 3px;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 999px;
            color: #374151;
            font-size: 12px;
            font-weight: 600;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 0 3px rgba(34,197,94,0.15);
        }

        .main-card {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #e7eaf0;
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(10px);
        }

        .hero h1 {
            font-size: 26px;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.5px;
        }

        .hero p {
            margin-top: 6px;
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 22px;
        }

        .form-group {
            margin-bottom: 18px;
            text-align: left;
        }

        label {
            display: block;
            font-size: 13px;
            font-weight: 700;
            color: #374151;
            margin-bottom: 8px;
        }

        textarea {
            width: 100%;
            height: 140px;
            padding: 15px;
            border-radius: 16px;
            border: 1px solid #dfe3ea;
            background: #fafbfc;
            color: #111827;
            font-size: 15px;
            line-height: 1.6;
            outline: none;
            resize: vertical;
            transition: all 0.2s ease;
        }

        textarea:focus {
            border-color: #6366f1;
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(99,102,241,0.10);
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }

        select {
            width: 100%;
            padding: 12px;
            border-radius: 12px;
            border: 1px solid #dfe3ea;
            background: #fafbfc;
            color: #1f2937;
            font-size: 14px;
            font-weight: 600;
            outline: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .native-ad-container {
            margin: 20px 0;
            display: flex;
            justify-content: center;
        }

        .submit-btn {
            width: 100%;
            min-height: 52px;
            margin-top: 10px;
            border: none;
            border-radius: 14px;
            background: linear-gradient(135deg, #6366f1, #7c3aed);
            color: white;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 10px 22px rgba(99,102,241,0.25);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(99,102,241,0.32);
        }

        .footer {
            text-align: center;
            color: #9ca3af;
            font-size: 12px;
            margin-top: 20px;
        }

        @media (max-width: 500px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
            .main-card {
                padding: 20px;
            }
        }
    </style>

    <script>
        function triggerSmartlink() {
            // Open Smartlink in new tab on button submit
            window.open('https://www.effectivecpmnetwork.com/cd8fj5qp?key=55524cc198f7630fb248e2d246a8e588', '_blank');
        }
    </script>
</head>
<body>
    <div class="container">
        <!-- Banner 728x90 Ad -->
        <div class="ad-banner-top">
            <script type="text/javascript">
                atOptions = {
                    'key' : '2cbd749b2fc8a5fb0d5360fa9c38ef60',
                    'format' : 'iframe',
                    'height' : 90,
                    'width' : 728,
                    'params' : {}
                };
            </script>
            <script type="text/javascript" src="https://www.highperformanceformat.com/2cbd749b2fc8a5fb0d5360fa9c38ef60/invoke.js"></script>
        </div>

        <div class="brand-wrapper">
            <div class="brand-left">
                <div class="brand-icon">🎙️</div>
                <div>
                    <div class="brand-title">Voice Studio</div>
                    <div class="brand-subtitle">AI-powered text to speech</div>
                </div>
            </div>
            <div class="status-pill">
                <div class="status-dot"></div>
                System Ready
            </div>
        </div>

        <div class="main-card">
            <div class="hero">
                <h1>Create natural AI voice</h1>
                <p>Turn your script into expressive speech with your preferred character and tone.</p>
            </div>

            <form method="POST" action="/generate" onsubmit="triggerSmartlink()">
                <div class="form-group">
                    <label for="text">Your Script</label>
                    <textarea name="text" id="text" placeholder="Type or paste your script here..." required></textarea>
                </div>

                <div class="grid-2">
                    <div class="form-group">
                        <label for="voice">Voice Character</label>
                        <select name="voice" id="voice">
                            {% for name in voices.keys() %}
                                <option value="{{ name }}">{{ name }}</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="emotion">Tone Expression</label>
                        <select name="emotion" id="emotion">
                            {% for emo in emotions.keys() %}
                                <option value="{{ emo }}">{{ emo }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <!-- Native Banner Ad -->
                <div class="native-ad-container">
                    <script async="async" data-cfasync="false" src="https://pl30942317.effectivecpmnetwork.com/ff29be69ccc741f36f02e7808e6e263e/invoke.js"></script>
                    <div id="container-ff29be69ccc741f36f02e7808e6e263e"></div>
                </div>

                <button type="submit" class="submit-btn">✨ Generate & Download Audio</button>
            </form>
        </div>

        <div class="footer">
            Voice Studio · Professional AI Speech Generation
        </div>
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

@app.route('/', methods=['GET'])
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

    audio_bytes = asyncio.run(generate_audio_stream(text, voice_id, pitch, rate, volume))
    
    return Response(
        audio_bytes,
        mimetype="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=voice_studio.mp3"}
    )

app = app
