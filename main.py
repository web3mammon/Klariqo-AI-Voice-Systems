#!/usr/bin/env python3
"""
KLARIQO MAIN APPLICATION - AUDIO FILE SERVING
Serves audio files directly without conversion
"""

import os
import json
import time 
import base64
import audioop
import threading
import io
import struct
import wave
import tempfile
import subprocess
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
from routes.exotel import exotel_bp

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
app.register_blueprint(exotel_bp)  # Enhanced Exotel routes with dynamic variable tracking

# Initialize Deepgram client
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY, config)

# Global variable for ngrok URL
current_ngrok_url = None

@app.route("/", methods=['GET'])
def health_check():
    """Health check endpoint"""
    return f"""
    <h1>🏫 AVS International School - AI Voice Assistant</h1>
    <p><strong>Status:</strong> ✅ Running</p>
    <p><strong>Active Sessions:</strong> {session_manager.get_active_count()}</p>
    <p><strong>Audio Files Cached:</strong> {len(audio_manager.memory_cache)}</p>
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
        "status": "Exotel Working - Direct audio streaming",
        "active_sessions": session_manager.get_active_count(),
        "cached_audio_files": len(audio_manager.cached_files),
        "endpoints": {
            "incoming": "/exotel/voice",
            "websocket_generator": "/exotel/get_websocket",
            "status": "/exotel/status",
            "websocket": "/exotel/media/<call_sid>"
        }
    }

# ===== AUDIO FILE SERVING FUNCTIONS =====

def convert_mp3_to_pcm_for_tts(mp3_data):
    """
    Convert MP3 from TTS to PCM format for Exotel
    Only used for TTS fallback - pre-recorded audio is already PCM
    """
    try:
        # Try using librosa for MP3 to PCM conversion
        import librosa
        import numpy as np
        
        # Load MP3 using librosa and convert to Exotel format
        audio_data, sr = librosa.load(io.BytesIO(mp3_data), sr=8000, mono=True)
        
        print(f"📊 TTS Audio: Converted to 8000Hz mono, {len(audio_data)} samples")
        
        # Convert to 16-bit PCM (Exotel format)
        audio_data = np.clip(audio_data, -1.0, 1.0)
        pcm_16bit = (audio_data * 32767).astype(np.int16)
        pcm_data = pcm_16bit.tobytes()
        
        print(f"✅ TTS converted to PCM: {len(pcm_data)} bytes")
        return pcm_data
        
    except ImportError:
        print("❌ librosa not available for TTS conversion")
        return None
    except Exception as e:
        print(f"❌ TTS MP3 to PCM conversion failed: {e}")
        return None

def send_audio_exotel_direct(ws, pcm_data, stream_sid):
    """
    Send PCM data directly to Exotel with proper chunking per Exotel specifications
    
    Exotel requirements:
    - Chunk size should be in multiples of 320 bytes
    - Minimum chunk size: 3.2k (100ms data)
    - Maximum chunk size: 100k
    - Format: 16-bit, 8kHz, mono PCM (little-endian), base64 encoded
    """
    try:
        if not stream_sid:
            print("❌ No stream_sid available")
            return
        
        if not pcm_data:
            print("❌ No PCM data provided")
            return
        
        print(f"🎵 Sending {len(pcm_data)} bytes of PCM data...")
        
        # Exotel chunk size requirements (multiples of 320 bytes)
        CHUNK_SIZE = 3200  # 100ms of audio data (minimum recommended)
        total_chunks = len(pcm_data) // CHUNK_SIZE
        
        print(f"🎵 Sending {total_chunks} chunks of {CHUNK_SIZE} bytes each")
        
        # Send chunks with proper timing
        for i in range(total_chunks):
            start_pos = i * CHUNK_SIZE
            end_pos = start_pos + CHUNK_SIZE
            chunk = pcm_data[start_pos:end_pos]
            
            # Send chunk to Exotel
            message = json.dumps({
                'event': 'media',
                'stream_sid': stream_sid,
                'media': {
                    'payload': base64.b64encode(chunk).decode("ascii")
                }
            })
            
            ws.send(message)
            time.sleep(0.02)  # 20ms delay between chunks
            
            if (i + 1) % 50 == 0:
                print(f"📡 Sent {i + 1}/{total_chunks} chunks...")
        
        # Handle remaining bytes (pad to 320-byte boundary)
        remaining_bytes = len(pcm_data) % CHUNK_SIZE
        if remaining_bytes > 0:
            last_chunk_start = total_chunks * CHUNK_SIZE
            last_chunk = pcm_data[last_chunk_start:]
            
            # Pad to nearest 320-byte boundary
            padding_needed = (320 - (len(last_chunk) % 320)) % 320
            last_chunk = last_chunk + b'\x00' * padding_needed
            
            message = json.dumps({
                'event': 'media',
                'stream_sid': stream_sid,
                'media': {
                    'payload': base64.b64encode(last_chunk).decode("ascii")
                }
            })
            
            ws.send(message)
            print(f"📡 Sent final padded chunk")
        
        print(f"✅ PCM audio sent successfully: {total_chunks} chunks")
        
    except Exception as e:
        print(f"❌ Send error: {e}")
        import traceback
        traceback.print_exc()

def process_and_respond_exotel_final(transcript, call_sid, ws, stream_sid):
    """Process input and respond with direct audio serving"""
    try:
        session = session_manager.get_session(call_sid)
        if not session:
            return
        
        start_time = time.time()
        
        # Log parent's input
        call_logger.log_parent_input(call_sid, transcript)
        
        # Get AI response
        response_type, content = response_router.get_school_response(transcript, session)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Add to history
        session.add_to_history("Parent", transcript)
        session.add_to_history("Nisha", f"<{response_type}: {content}>")
        
        # Clean logging
        print(f"📞 User: {transcript}")
        print(f"🤖 AI: {content} ({response_time_ms}ms)")
        
        if response_type == "AUDIO":
            # Send PCM audio files directly
            audio_files = [f.strip() for f in content.split('+')]
            
            for audio_file in audio_files:
                # Ensure we use .mp3 extension for cache lookup (audio manager uses .mp3 keys)
                cache_key = audio_file.replace('.pcm', '.mp3') if audio_file.endswith('.pcm') else audio_file
                
                if cache_key in audio_manager.memory_cache:
                    pcm_data = audio_manager.memory_cache[cache_key]
                    
                    # Send PCM data directly to Exotel
                    send_audio_exotel_direct(ws, pcm_data, stream_sid)
                    time.sleep(1.0)
                else:
                    print(f"❌ PCM audio file not in cache: {cache_key} (original: {audio_file})")
                    
            call_logger.log_nisha_audio_response(call_sid, content)
            
        elif response_type == "TTS":
            # Generate TTS and convert MP3 to PCM for Exotel
            tts_audio_data = tts_engine.generate_audio(content, save_temp=False)
            if tts_audio_data:
                # Convert MP3 from ElevenLabs to PCM for Exotel
                pcm_data = convert_mp3_to_pcm_for_tts(tts_audio_data)
                if pcm_data:
                    send_audio_exotel_direct(ws, pcm_data, stream_sid)
                else:
                    print("❌ TTS MP3 to PCM conversion failed")
                    
            call_logger.log_nisha_tts_response(call_sid, content)
        
        print(f"✅ Response sent")
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()

# ===== EXOTEL WEBSOCKET HANDLER =====

@sock.route('/exotel/media/<call_sid>')
def exotel_media_stream(ws, call_sid):
    """Handle Exotel WebSocket - Direct audio streaming"""
    
    session = session_manager.get_session(call_sid)
    if not session:
        session = session_manager.create_session(call_sid, "inbound")
    
    session.twilio_ws = ws
    session.stream_sid = None
    
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
                process_and_respond_exotel_final(session.completed_transcript, call_sid, ws, session.stream_sid)
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
        
        # Log parent's input
        call_logger.log_parent_input(call_sid, transcript)
        
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

@app.route("/audio_pcm/<filename>")
def serve_audio(filename):
    """Serve PCM audio files from memory cache"""
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

def test_audio_cache():
    """Test audio cache availability"""
    try:
        if audio_manager.memory_cache:
            test_file = list(audio_manager.memory_cache.keys())[0]
            audio_data = audio_manager.memory_cache[test_file]
            
            print(f"🧪 Testing audio cache with {test_file}")
            
            if audio_data and len(audio_data) > 0:
                print(f"✅ Audio file loaded: {len(audio_data)} bytes")
                return True
            else:
                print("❌ Audio file empty or invalid")
                return False
        else:
            print("⚠️ No audio files in cache to test")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

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
    print("🚀 KLARIQO - AI Voice Agent (Direct Audio Serving)")
    print("=" * 40)
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Config OK")
    except ValueError as e:
        print(f"❌ Config error: {e}")
        exit(1)
    
    # Test audio cache during startup
    print("🧪 Testing audio cache...")
    if test_audio_cache():
        print("✅ Audio cache working!")
    else:
        print("⚠️ Audio cache issues detected")
    
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
        print("   ✅ Direct audio streaming")
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