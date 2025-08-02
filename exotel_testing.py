#!/usr/bin/env python3
"""
MINIMAL EXOTEL TEST SCRIPT
Tests basic Exotel flow: Intro → User speaks → Play test.mp3
NO GPT, NO CONVERSION, NO TTS - just pure audio playback test
"""

import os
import json
import time 
import base64
import threading
from flask import Flask, request
from flask_sock import Sock
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents, 
    LiveOptions
)

# Your API keys (update these)
DEEPGRAM_API_KEY = "eb1d2caf340731b7ae359375a2fb67f45be97935"

app = Flask(__name__)
sock = Sock(app)

# Initialize Deepgram
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, config)

# Simple session storage
active_sessions = {}

class SimpleSession:
    def __init__(self, call_sid):
        self.call_sid = call_sid
        self.accumulated_text = ""
        self.last_activity_time = None
        self.dg_connection = None
        self.stream_sid = None
        
    def on_deepgram_message(self, *args, **kwargs):
        result = kwargs.get('result')
        if result is None:
            return
            
        sentence = result.channel.alternatives[0].transcript
        is_final = result.is_final
        
        if sentence.strip():
            self.last_activity_time = time.time()
            if is_final:
                if self.accumulated_text:
                    self.accumulated_text += " " + sentence
                else:
                    self.accumulated_text = sentence
    
    def on_deepgram_error(self, *args, **kwargs):
        print(f"❌ Deepgram error: {kwargs}")
    
    def on_deepgram_open(self, *args, **kwargs):
        pass
    
    def check_for_completion(self):
        if (self.accumulated_text and 
            self.last_activity_time and 
            time.time() - self.last_activity_time >= 0.4):  # 400ms silence
            
            completed = self.accumulated_text
            self.accumulated_text = ""
            self.last_activity_time = None
            return completed
        return None

@app.route("/", methods=['GET'])
def health():
    return "<h1>🧪 Minimal Exotel Test</h1><p>Ready for testing!</p>"

@app.route("/exotel/voice", methods=['POST'])
def handle_exotel_incoming():
    """Handle incoming call - play intro then go to WebSocket"""
    
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"📞 TEST CALL: {call_sid} from {from_number}")
    
    # Create simple session
    session = SimpleSession(call_sid)
    active_sessions[call_sid] = session
    
    # Use HTTPS endpoint for WebSocket URL  
    websocket_endpoint = f"https://{request.host}/exotel/get_websocket"
    
    # Play intro then go to WebSocket
    exotel_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>https://{request.host}/static/intro.mp3</Play>
    <Voicebot url="{websocket_endpoint}" />
</Response>"""
    
    return exotel_response, 200, {'Content-Type': 'application/xml'}

@app.route("/exotel/get_websocket", methods=['GET'])
def get_websocket_url():
    """Return WebSocket URL"""
    call_sid = request.args.get('CallSid')
    
    if not call_sid:
        return {"error": "Missing CallSid"}, 400
    
    websocket_url = f"wss://{request.host}/exotel/media/{call_sid}"
    print(f"🔗 WebSocket URL: {websocket_url}")
    
    return {"url": websocket_url}, 200

@sock.route('/exotel/media/<call_sid>')
def test_websocket(ws, call_sid):
    """Minimal WebSocket handler - just transcribe and play test.mp3"""
    
    print(f"🔌 WebSocket connected: {call_sid}")
    
    session = active_sessions.get(call_sid)
    if not session:
        print(f"❌ No session for {call_sid}")
        return
    
    # Start Deepgram for transcription
    def start_deepgram():
        try:
            options = LiveOptions(
                model="nova-2",
                language="hi",  # Hindi + English
                punctuate=True,
                smart_format=True,
                sample_rate=8000,
                encoding="linear16",
                channels=1,
                interim_results=True,
            )
            
            session.dg_connection = deepgram_client.listen.websocket.v("1")
            session.dg_connection.on(LiveTranscriptionEvents.Transcript, session.on_deepgram_message)
            session.dg_connection.on(LiveTranscriptionEvents.Error, session.on_deepgram_error)
            session.dg_connection.start(options)
            
        except Exception as e:
            print(f"❌ Deepgram setup failed: {e}")
    
    # Start transcription
    transcript_thread = threading.Thread(target=start_deepgram)
    transcript_thread.daemon = True
    transcript_thread.start()
    time.sleep(0.5)
    
    # Monitor for completed transcripts
    def transcript_monitor():
        while True:
            time.sleep(0.1)
            completed = session.check_for_completion()
            if completed:
                print(f"📝 USER SAID: {completed}")
                play_test_audio(ws, session.stream_sid)
                # Reset for next input
                break
    
    monitor_thread = threading.Thread(target=transcript_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                print(f"✅ Connected: {call_sid}")
                
            elif event == 'start':
                session.stream_sid = data.get('stream_sid')
                print(f"🎤 Stream started: {session.stream_sid}")
                
            elif event == 'media':
                # Forward audio to Deepgram
                if session.dg_connection:
                    payload = data.get('media', {}).get('payload')
                    if payload:
                        try:
                            audio_data = base64.b64decode(payload)
                            session.dg_connection.send(audio_data)
                        except Exception as e:
                            print(f"⚠️ Audio error: {e}")
                            
            elif event == 'stop':
                print(f"🛑 Stream stopped")
                break
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        
    finally:
        if session.dg_connection:
            session.dg_connection.finish()

def play_test_audio(ws, stream_sid):
    """Play test.mp3 file directly without any conversion"""
    
    print(f"🎵 Playing test audio...")
    
    if not stream_sid:
        print("❌ No stream_sid")
        return
    
    # Method 1: Try to load test.mp3 and send as-is
    test_files = ["test.mp3", "test.pcm", "test.wav"]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"📁 Found {test_file}, attempting to play...")
            
            try:
                with open(test_file, 'rb') as f:
                    audio_data = f.read()
                
                # Method A: Send raw file data (no conversion)
                send_raw_audio_chunks(ws, audio_data, stream_sid, test_file)
                return
                
            except Exception as e:
                print(f"❌ Failed to play {test_file}: {e}")
                continue
    
    # Method 2: Generate silence if no test file found
    print("📢 No test file found, generating silence...")
    silence_data = b'\x00' * 8000  # 1 second of silence (8kHz)
    send_raw_audio_chunks(ws, silence_data, stream_sid, "silence")

def send_raw_audio_chunks(ws, audio_data, stream_sid, filename):
    """Send audio data in chunks to Exotel"""
    
    try:
        CHUNK_SIZE = 800  # 100ms at 8kHz
        total_chunks = len(audio_data) // CHUNK_SIZE
        
        print(f"🔊 Sending {filename}: {len(audio_data)} bytes, {total_chunks} chunks")
        
        for i in range(0, len(audio_data), CHUNK_SIZE):
            chunk = audio_data[i:i + CHUNK_SIZE]
            
            # Pad chunk if needed
            if len(chunk) < CHUNK_SIZE:
                chunk = chunk + b'\x00' * (CHUNK_SIZE - len(chunk))
            
            # Send chunk to Exotel
            message = json.dumps({
                'event': 'media',
                'stream_sid': stream_sid,
                'media': {
                    'payload': base64.b64encode(chunk).decode('ascii')
                }
            })
            
            ws.send(message)
            time.sleep(0.1)  # 100ms delay
        
        print(f"✅ {filename} sent successfully!")
        
    except Exception as e:
        print(f"❌ Send error: {e}")

# Static file serving for intro
@app.route("/static/<filename>")
def serve_static(filename):
    """Serve static files"""
    
    # Create a simple intro if it doesn't exist
    if filename == "intro.mp3" and not os.path.exists("intro.mp3"):
        return "Welcome to Klariqo test. Please say something.", 200, {'Content-Type': 'text/plain'}
    
    try:
        from flask import send_file
        return send_file(filename)
    except:
        return f"File {filename} not found", 404

def start_ngrok():
    """Start ngrok"""
    import subprocess
    import urllib.request
    
    try:
        print("🚀 Starting ngrok...")
        process = subprocess.Popen(['ngrok', 'http', '5000'])
        time.sleep(3)
        
        # Get tunnel URL
        with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
            data = json.loads(response.read())
            for tunnel in data['tunnels']:
                if tunnel.get('proto') == 'https':
                    return tunnel['public_url']
        
        return None
    except:
        return None

if __name__ == "__main__":
    print("🧪 MINIMAL EXOTEL TEST SCRIPT")
    print("=" * 40)
    print("Flow: Intro → User speaks → Play test.mp3")
    print("NO GPT, NO CONVERSION, NO TTS")
    print()
    
    # Create test files if they don't exist
    if not os.path.exists("test.mp3"):
        print("📝 Creating test.mp3 (silence)...")
        silence = b'\x00' * 8000  # 1 second silence
        with open("test.mp3", 'wb') as f:
            f.write(silence)
    
    # Start ngrok
    public_url = start_ngrok()
    
    if public_url:
        print(f"🌐 Public URL: {public_url}")
        print(f"📞 EXOTEL SETUP:")
        print(f"   Incoming Call URL: {public_url}/exotel/voice")
        print(f"   WebSocket URL: {public_url}/exotel/get_websocket")
        print()
        print("🧪 TEST INSTRUCTIONS:")
        print("1. Configure Exotel with the above URLs")
        print("2. Call your Exotel number")
        print("3. After intro, say something")
        print("4. Should hear test.mp3 play back")
        print()
        print("🔍 If this works → Audio conversion is the issue")
        print("🔍 If this fails → WebSocket/Exotel setup issue")
    else:
        print("⚠️ ngrok failed, running on localhost:5000")
    
    print("✅ Starting minimal test server...")
    print("=" * 40)
    
    app.run(host='0.0.0.0', port=5000, debug=False)