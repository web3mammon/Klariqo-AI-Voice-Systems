#!/usr/bin/env python3
"""
KLARIQO MAIN APPLICATION - FIXED FOR EXOTEL
Based on official Exotel WebSocket example
"""

import os
import json
import time 
import base64
import audioop
import threading
import io
import shutil
from flask import Flask, request, send_file
from flask_sock import Sock
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents, 
    LiveOptions
)

# Import our modular components
from config import Config
from session import session_manager
from router import response_router
from tts_engine import tts_engine
from audio_manager import audio_manager
from logger import call_logger

# Import route blueprints
from routes.inbound import inbound_bp
from routes.outbound import outbound_bp
from routes.test import test_bp

# Initialize Flask app with WebSocket support
app = Flask(__name__)
sock = Sock(app)

# Configure Flask logging to be less verbose
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

audio_manager.reload_library()

# Register route blueprints
app.register_blueprint(inbound_bp)
app.register_blueprint(outbound_bp, url_prefix='/outbound')
app.register_blueprint(test_bp)

# Initialize Deepgram client
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY, config)

# Global variable for ngrok URL
current_ngrok_url = None

@app.route("/", methods=['GET'])
def health_check():
    """Health check endpoint"""
    return f"""
    <h1>🚀 Klariqo - AI Voice Agent</h1>
    <p><strong>Status:</strong> ✅ Running</p>
    <p><strong>Active Sessions:</strong> {session_manager.get_active_count()}</p>
    <br>    
    <p><a href="/test">🧪 Test Page</a></p>
    <p><a href="/exotel/debug">🔧 Exotel Debug</a></p>
    """

# ===== EXOTEL ROUTES =====

@app.route("/exotel/voice", methods=['POST'])
def handle_exotel_incoming():
    """Handle incoming call from Exotel"""
    
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"📞 Exotel call: {call_sid}")
    
    if not call_sid:
        print("❌ No CallSid received")
        return "Error: No CallSid", 400
    
    # Create session
    session = session_manager.create_session(call_sid, "inbound")
    session.session_memory["intro_played"] = True
    
    # Log call start
    call_logger.log_call_start(call_sid, from_number, "inbound")
    
    # Use HTTPS endpoint for dynamic WebSocket URL generation  
    websocket_endpoint = f"https://{request.host}/exotel/get_websocket"
    
    exotel_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Voicebot url="{websocket_endpoint}" />
</Response>"""
    
    return exotel_response, 200, {'Content-Type': 'application/xml'}

@app.route("/exotel/get_websocket", methods=['GET'])
def get_dynamic_websocket_url():
    """Return dynamic WebSocket URL as JSON per Exotel spec"""
    
    call_sid = request.args.get('CallSid')
    
    if not call_sid:
        return {"error": "Missing CallSid"}, 400
    
    # Generate WebSocket URL
    websocket_url = f"wss://{request.host}/exotel/media/{call_sid}"
    
    print(f"🔗 WebSocket: {websocket_url}")
    
    return {
        "url": websocket_url
    }, 200, {'Content-Type': 'application/json'}

@app.route("/exotel/status", methods=['POST'])
def exotel_call_status():
    """Handle Exotel call status updates"""
    
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    print(f"📞 Status: {call_sid} → {call_status}")
    
    if call_status in ['completed', 'failed', 'busy', 'no-answer']:
        call_logger.log_call_end(call_sid, call_status)
        session_manager.remove_session(call_sid)
    
    return "OK", 200

@app.route("/exotel/debug", methods=['GET'])
def exotel_debug():
    """Debug endpoint"""
    
    return {
        "status": "Exotel Fixed - Official Format",
        "active_sessions": session_manager.get_active_count(),
        "cached_audio_files": len(audio_manager.cached_files),
        "endpoints": {
            "incoming": "/exotel/voice",
            "websocket_generator": "/exotel/get_websocket",
            "status": "/exotel/status",
            "websocket": "/exotel/media/<call_sid>"
        }
    }

# ===== AUDIO CONVERSION FUNCTIONS =====

def setup_ffmpeg_windows():
    """Automatically setup FFmpeg on Windows"""
    import subprocess
    import urllib.request
    import zipfile
    import tempfile
    
    print("📦 Setting up FFmpeg for Windows...")
    
    try:
        # Check if FFmpeg already exists
        if shutil.which('ffmpeg'):
            print("✅ FFmpeg already available in PATH")
            return True
        
        # Create ffmpeg directory in project
        ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg_portable")
        os.makedirs(ffmpeg_dir, exist_ok=True)
        
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        
        if os.path.exists(ffmpeg_exe):
            print("✅ Portable FFmpeg already exists")
            # Add to PATH for current session
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            return True
        
        # Download portable FFmpeg
        print("📥 Downloading portable FFmpeg...")
        download_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            urllib.request.urlretrieve(download_url, tmp_file.name)
            
            print("📦 Extracting FFmpeg...")
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                # Find ffmpeg.exe in the zip
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('ffmpeg.exe'):
                        # Extract just the exe
                        with zip_ref.open(file_info) as source:
                            with open(ffmpeg_exe, 'wb') as target:
                                target.write(source.read())
                        break
            
            # Cleanup
            os.unlink(tmp_file.name)
        
        if os.path.exists(ffmpeg_exe):
            # Add to PATH for current session
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            print("✅ Portable FFmpeg setup complete!")
            return True
        else:
            print("❌ FFmpeg extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ FFmpeg setup failed: {e}")
        return False

def initialize_audio_dependencies():
    """Initialize audio processing dependencies"""
    
    # Try to import pydub
    try:
        from pydub import AudioSegment
        print("✅ pydub available")
        
        # Test conversion
        test_successful = True
        try:
            # Create a tiny test audio
            test_audio = AudioSegment.silent(duration=100)  # 100ms silence
            test_audio = test_audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)
            test_pcm = test_audio.raw_data
            print("✅ Audio conversion test passed")
        except Exception as e:
            print(f"⚠️ Audio conversion test failed: {e}")
            test_successful = False
            
        if not test_successful:
            # Try to setup FFmpeg
            if os.name == 'nt':  # Windows
                setup_ffmpeg_windows()
            else:
                print("💡 Install FFmpeg: sudo apt install ffmpeg (Linux) or brew install ffmpeg (Mac)")
        
    except ImportError:
        print("📦 Installing pydub...")
        import subprocess
        subprocess.check_call(["pip", "install", "pydub"])
        print("✅ pydub installed")

def convert_mp3_to_pcm_simple(mp3_data):
    """Convert MP3 to PCM for Exotel using multiple fallback methods"""
    try:
        # Method 1: Try pydub with FFmpeg
        try:
            from pydub import AudioSegment
            
            # Load MP3 from bytes
            audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            
            # Convert to Exotel format: 8kHz, 16-bit, mono
            audio = audio.set_frame_rate(8000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Return raw PCM data
            return audio.raw_data
            
        except Exception as e:
            print(f"⚠️ pydub failed: {e}")
            raise
            
    except ImportError:
        print("⚠️ pydub not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "pydub"])
        # Retry after installation
        return convert_mp3_to_pcm_simple(mp3_data)
        
    except Exception as e:
        print(f"❌ All conversion methods failed: {e}")
        # Method 2: Use librosa as fallback (if available)
        try:
            import librosa
            import numpy as np
            
            # Load audio using librosa
            audio_data, sr = librosa.load(io.BytesIO(mp3_data), sr=8000, mono=True)
            
            # Convert to 16-bit PCM
            pcm_data = (audio_data * 32767).astype(np.int16).tobytes()
            
            print("✅ Converted using librosa fallback")
            return pcm_data
            
        except ImportError:
            print("❌ librosa not available")
        except Exception as e:
            print(f"❌ librosa conversion failed: {e}")
        
        # Method 3: Bypass conversion entirely (emergency fallback)
        print("⚠️ Using MP3 data directly - audio quality may be poor")
        return mp3_data

# ===== FIXED EXOTEL WEBSOCKET HANDLER =====

@sock.route('/exotel/media/<call_sid>')
def exotel_media_stream(ws, call_sid):
    """Handle Exotel WebSocket - FIXED based on official example"""
    
    session = session_manager.get_session(call_sid)
    if not session:
        session = session_manager.create_session(call_sid, "inbound")
    
    session.twilio_ws = ws
    session.stream_sid = None  # Will be set from start message
    
    def start_deepgram():
        """Initialize Deepgram connection"""
        try:
            options = LiveOptions(
                model=Config.DEEPGRAM_MODEL,
                language=Config.DEEPGRAM_LANGUAGE,
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
            session.dg_connection.on(LiveTranscriptionEvents.Open, session.on_deepgram_open)
            session.dg_connection.start(options)
            
        except Exception as e:
            print(f"❌ Deepgram error: {e}")
    
    # Start Deepgram
    deepgram_thread = threading.Thread(target=start_deepgram)
    deepgram_thread.daemon = True
    deepgram_thread.start()
    time.sleep(0.5)
    
    def transcript_checker():
        """Monitor for completed transcripts"""
        while True:
            time.sleep(0.05)
            if session.check_for_completion():
                process_and_respond_exotel_official(session.completed_transcript, call_sid, ws, session.stream_sid)
                session.reset_for_next_input()
    
    checker_thread = threading.Thread(target=transcript_checker)
    checker_thread.daemon = True
    checker_thread.start()
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            event_type = data.get('event')
            
            if event_type == 'connected':
                print(f"🔌 Exotel connected: {call_sid}")
                
            elif event_type == 'start':
                # CRITICAL: Get stream_sid from start message
                session.stream_sid = data.get('stream_sid')
                print(f"🎤 Stream started: {session.stream_sid}")
                
            elif event_type == 'media':
                if session.dg_connection:
                    media_payload = data.get('media', {}).get('payload')
                    if media_payload:
                        try:
                            linear_data = base64.b64decode(media_payload)
                            session.dg_connection.send(linear_data)
                        except Exception as e:
                            print(f"⚠️ Audio error: {e}")
                            
            elif event_type == 'stop':
                print(f"🛑 Stream stopped: {call_sid}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        
    finally:
        if session.dg_connection:
            session.dg_connection.finish()
            session.dg_connection = None

def process_and_respond_exotel_official(transcript, call_sid, ws, stream_sid):
    """Process input and respond using Exotel's official format"""
    try:
        session = session_manager.get_session(call_sid)
        if not session:
            return
        
        start_time = time.time()
        
        # Log principal's input
        call_logger.log_principal_input(call_sid, transcript)
        
        # Get AI response
        response_type, content = response_router.get_school_response(transcript, session)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Add to history
        session.add_to_history("Principal", transcript)
        session.add_to_history("Nisha", f"<{response_type}: {content}>")
        
        # Clean logging
        print(f"📞 User: {transcript}")
        print(f"🤖 AI: {content} ({response_time_ms}ms)")
        
        if response_type == "AUDIO":
            # Send audio files using official Exotel format
            audio_files = [f.strip() for f in content.split('+')]
            
            for audio_file in audio_files:
                if audio_file in audio_manager.memory_cache:
                    mp3_data = audio_manager.memory_cache[audio_file]
                    
                    # Convert MP3 to PCM for Exotel
                    pcm_data = convert_mp3_to_pcm_simple(mp3_data)
                    if pcm_data:
                        send_audio_exotel_official(ws, pcm_data, stream_sid)
                    else:
                        print(f"❌ Failed to convert {audio_file}")
                    
                    # Delay between files
                    time.sleep(0.5)
                else:
                    print(f"❌ Audio file not in cache: {audio_file}")
                    
            call_logger.log_nisha_audio_response(call_sid, content)
            
        elif response_type == "TTS":
            # Generate TTS and send
            tts_audio_data = tts_engine.generate_audio(content, save_temp=False)
            if tts_audio_data:
                pcm_data = convert_mp3_to_pcm_simple(tts_audio_data)
                if pcm_data:
                    send_audio_exotel_official(ws, pcm_data, stream_sid)
                    
            call_logger.log_nisha_tts_response(call_sid, content)
        
        print(f"✅ Response sent")
        
    except Exception as e:
        print(f"❌ Processing error: {e}")

def send_audio_exotel_official(ws, pcm_data, stream_sid):
    """Send audio using EXACT Exotel official format"""
    try:
        if not stream_sid:
            print("❌ No stream_sid available")
            return
            
        # Use exact parameters from Exotel example
        RATE = 8000
        CHUNK_SIZE = int(RATE / 10)  # 100ms chunks = 800 bytes
        
        print(f"🎵 Sending {len(pcm_data)} bytes in {CHUNK_SIZE}-byte chunks")
        
        for i in range(0, len(pcm_data), CHUNK_SIZE):
            chunk = pcm_data[i:i + CHUNK_SIZE]
            
            # Pad last chunk if needed
            if len(chunk) < CHUNK_SIZE:
                chunk = chunk + b'\x00' * (CHUNK_SIZE - len(chunk))
            
            # Use EXACT format from Exotel example
            message = json.dumps({
                'event': 'media',
                'stream_sid': stream_sid,
                'media': {
                    'payload': base64.b64encode(chunk).decode("ascii")
                }
            })
            
            # Use EXACT timing from Exotel example
            time.sleep(0.25)
            ws.send(message)
            time.sleep(0.20)
            
        print(f"✅ Audio sent successfully")
        
    except Exception as e:
        print(f"❌ Send error: {e}")

# ===== TWILIO WEBSOCKET (KEEP FOR BACKWARDS COMPATIBILITY) =====

@sock.route('/media/<call_sid>')
def media_stream(ws, call_sid):
    """Handle Twilio streaming audio"""
    session = session_manager.get_session(call_sid)
    if not session:
        return
    
    session.twilio_ws = ws
    
    def start_deepgram():
        """Initialize Deepgram connection for this session"""
        try:
            options = LiveOptions(
                model=Config.DEEPGRAM_MODEL,
                language=Config.DEEPGRAM_LANGUAGE,
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
            session.dg_connection.on(LiveTranscriptionEvents.Open, session.on_deepgram_open)
            session.dg_connection.start(options)
            
        except Exception as e:
            print(f"❌ Deepgram setup error: {e}")
    
    # Start Deepgram in separate thread
    deepgram_thread = threading.Thread(target=start_deepgram)
    deepgram_thread.daemon = True
    deepgram_thread.start()
    time.sleep(0.5)
    
    def transcript_checker():
        """Monitor for completed transcripts"""
        while True:
            time.sleep(0.05)
            if session.check_for_completion():
                redirect_to_processing(session.completed_transcript, call_sid)
                break
    
    # Start transcript checker
    checker_thread = threading.Thread(target=transcript_checker)
    checker_thread.daemon = True
    checker_thread.start()
    
    try:
        # Handle WebSocket messages from Twilio
        while True:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            
            if data.get('event') == 'media':
                # Forward audio to Deepgram
                if session.dg_connection:
                    media_payload = data.get('media', {}).get('payload', '')
                    if media_payload:
                        try:
                            # Convert μ-law to linear PCM for Deepgram
                            mulaw_data = base64.b64decode(media_payload)
                            linear_data = audioop.ulaw2lin(mulaw_data, 2)
                            session.dg_connection.send(linear_data)
                        except Exception as e:
                            print(f"⚠️ Audio processing error: {e}")
                            
            elif data.get('event') == 'stop':
                break
                
    except Exception as e:
        print(f"❌ WebSocket error for {call_sid}: {e}")
        
    finally:
        # Cleanup session
        if session.dg_connection:
            session.dg_connection.finish()
            session.dg_connection = None

def redirect_to_processing(transcript, call_sid):
    """Process user input and prepare response for Twilio"""
    try:
        session = session_manager.get_session(call_sid)
        if not session:
            return
        
        start_time = time.time()
        
        # Log principal's input
        call_logger.log_principal_input(call_sid, transcript)
        
        # Get AI response
        response_type, content = response_router.get_school_response(transcript, session)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Generate TTS if needed
        if response_type == "TTS":
            temp_filename = tts_engine.generate_audio(content, save_temp=True)
            if not temp_filename:
                print(f"❌ TTS generation failed for: {content}")
                return
        
        # Prepare session for TwiML generation
        session.next_response_type = response_type
        session.next_response_content = content
        session.next_transcript = transcript
        session.ready_for_twiml = True
        
        # Clean logging
        direction_emoji = "📞" if session.call_direction == "inbound" else "🏫"
        
        if response_type == "AUDIO":
            print(f"{direction_emoji} User: {transcript}")
            print(f"{direction_emoji} GPT Response: {content} ({response_time_ms}ms)")
        else:
            print(f"{direction_emoji} User: {transcript}")
            print(f"{direction_emoji} TTS Response: {content} ({response_time_ms}ms)")
        
        # Redirect call to continue endpoint
        global current_ngrok_url
        if current_ngrok_url:
            from twilio.rest import Client
            twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            
            if session.call_direction == "outbound":
                continue_url = f"{current_ngrok_url}/outbound/twilio/continue/{call_sid}"
            else:
                continue_url = f"{current_ngrok_url}/twilio/continue/{call_sid}"
                
            twilio_client.calls(call_sid).update(url=continue_url, method='POST')
            
    except Exception as e:
        print(f"❌ Processing error for {call_sid}: {e}")

@app.route("/audio_optimised/<filename>")
def serve_audio(filename):
    """Serve audio files from memory cache"""
    return audio_manager.serve_audio_file(filename)

@app.route("/temp/<filename>")
def serve_temp_audio(filename):
    """Serve temporary TTS audio files"""
    try:
        if filename.startswith("temp_tts_"):
            file_path = os.path.join(Config.TEMP_FOLDER, filename)
            if os.path.exists(file_path):
                return send_file(file_path, mimetype='audio/mpeg')
            else:
                return "TTS file not found", 404
        else:
            return "Invalid file type", 404
            
    except Exception as e:
        print(f"❌ Error serving TTS audio {filename}: {e}")
        return "Error serving TTS audio", 500

@app.route("/logs/<filename>")
def serve_logs(filename):
    """Serve log files for download"""
    try:
        file_path = os.path.join(Config.LOGS_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return "Log file not found", 404
    except Exception as e:
        return f"Error serving log: {e}", 500

def start_ngrok():
    """Start ngrok tunnel for local development"""
    import subprocess
    import urllib.request
    
    try:
        # First check if ngrok is already running
        try:
            with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
                data = json.loads(response.read())
                if 'tunnels' in data and len(data['tunnels']) > 0:
                    for tunnel in data['tunnels']:
                        if tunnel.get('proto') == 'https':
                            return tunnel['public_url']
        except:
            pass
        
        print("🚀 Starting ngrok...")
        process = subprocess.Popen([
            'ngrok', 'http', str(Config.FLASK_PORT)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(5)
        
        # Try to get tunnel info
        for attempt in range(10):
            try:
                with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
                    data = json.loads(response.read())
                    
                    if 'tunnels' not in data:
                        time.sleep(1)
                        continue
                        
                    tunnels = data['tunnels']
                    if len(tunnels) == 0:
                        time.sleep(1)
                        continue
                    
                    # Find HTTPS tunnel
                    for tunnel in tunnels:
                        if tunnel.get('proto') == 'https':
                            return tunnel['public_url']
                    
                    # Fallback to first tunnel
                    if tunnels:
                        return tunnels[0]['public_url']
                        
            except Exception as e:
                time.sleep(1)
        
        print("❌ Could not get ngrok URL")
        return None
            
    except FileNotFoundError:
        print("⚠️ ngrok not found")
        return None
    except Exception as e:
        print(f"⚠️ ngrok error: {e}")
        return None

def cleanup_temp_files():
    """Periodic cleanup of temporary files"""
    while True:
        time.sleep(3600)
        tts_engine.cleanup_temp_files()

if __name__ == "__main__":
    initialize_audio_dependencies()  # Initialize audio dependencies first

    print("🚀 KLARIQO - AI Voice Agent")
    print("=" * 40)
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Config OK")
    except ValueError as e:
        print(f"❌ Config error: {e}")
        exit(1)
    
    # Start ngrok
    public_url = start_ngrok()
    current_ngrok_url = public_url
    
    if public_url:
        print(f"🌐 Public URL: {public_url}")
        print()
        print("📞 EXOTEL SETUP:")
        print(f"   Incoming Call URL: {public_url}/exotel/voice")
        print(f"   Voicebot URL: {public_url}/exotel/get_websocket")
        print()
        print("🔧 EXOTEL FLOW:")
        print("   Greeting → Voicebot")
        print("   ✅ YES, that's correct!")
        print()
    else:
        print("⚠️ Running without ngrok")
    
    print("✅ READY!")
    print("=" * 40)
    
    # Start background cleanup
    cleanup_thread = threading.Thread(target=cleanup_temp_files)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # Run Flask app
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
        threaded=True
    )