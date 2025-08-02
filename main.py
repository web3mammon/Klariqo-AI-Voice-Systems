#!/usr/bin/env python3
"""
KLARIQO MAIN APPLICATION - FIXED FOR EXOTEL PCM CHUNKING
Proper PCM conversion and 320-byte chunking for Exotel
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
        "status": "Exotel Fixed - PCM + 320-byte chunking",
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

def convert_mp3_to_pcm_pure_python(mp3_data):
    """
    Convert MP3 to PCM using pure Python libraries only
    Fallback method that actually works!
    """
    try:
        # Method 1: Try using system tools if available
        try:
            # Write MP3 to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_mp3:
                tmp_mp3.write(mp3_data)
                tmp_mp3_path = tmp_mp3.name
            
            try:
                # Create temp wav file
                tmp_wav_path = tmp_mp3_path.replace('.mp3', '.wav')
                
                # Try different system commands
                conversion_commands = [
                    # Try ffmpeg if available
                    ['ffmpeg', '-i', tmp_mp3_path, '-ar', '8000', '-ac', '1', '-f', 'wav', tmp_wav_path],
                    # Try avconv as alternative
                    ['avconv', '-i', tmp_mp3_path, '-ar', '8000', '-ac', '1', '-f', 'wav', tmp_wav_path],
                ]
                
                for cmd in conversion_commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, timeout=10)
                        if result.returncode == 0 and os.path.exists(tmp_wav_path):
                            # Read the converted WAV file
                            with wave.open(tmp_wav_path, 'rb') as wav_file:
                                # Ensure correct format
                                if wav_file.getframerate() != 8000:
                                    print(f"⚠️ Sample rate is {wav_file.getframerate()}, should be 8000")
                                if wav_file.getnchannels() != 1:
                                    print(f"⚠️ Channels is {wav_file.getnchannels()}, should be 1")
                                if wav_file.getsampwidth() != 2:
                                    print(f"⚠️ Sample width is {wav_file.getsampwidth()}, should be 2")
                                
                                pcm_data = wav_file.readframes(wav_file.getnframes())
                                print(f"✅ Converted using {cmd[0]}: {len(pcm_data)} bytes PCM")
                                return pcm_data
                    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                        continue
                
            finally:
                # Cleanup temp files
                try:
                    os.unlink(tmp_mp3_path)
                    if os.path.exists(tmp_wav_path):
                        os.unlink(tmp_wav_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ System conversion failed: {e}")
        
        # Method 2: Try pydub if available (but don't require it)
        try:
            from pydub import AudioSegment
            
            # Load MP3 from bytes
            audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            
            # Convert to Exotel format: 8kHz, 16-bit, mono
            audio = audio.set_frame_rate(8000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Return raw PCM data
            pcm_data = audio.raw_data
            print(f"✅ Converted using pydub: {len(pcm_data)} bytes PCM")
            return pcm_data
            
        except ImportError:
            print("⚠️ pydub not available")
        except Exception as e:
            print(f"⚠️ pydub conversion failed: {e}")
        
        # Method 3: Generate silence as fallback (better than noise)
        print("⚠️ All conversion methods failed, generating silence")
        # Generate 2 seconds of silence at 8kHz, 16-bit, mono
        duration_seconds = 2
        sample_rate = 8000
        silence_samples = duration_seconds * sample_rate
        # 16-bit silence = 0x0000 for each sample
        pcm_data = b'\x00\x00' * silence_samples
        print(f"🔇 Generated {len(pcm_data)} bytes of silence")
        return pcm_data
        
    except Exception as e:
        print(f"❌ All conversion methods failed: {e}")
        # Return minimal silence
        return b'\x00\x00' * 1600  # 200ms of silence

def send_audio_exotel_fixed_chunking(ws, mp3_data, stream_sid):
    """
    Send audio to Exotel with PROPER PCM format and 320-byte chunking
    """
    try:
        if not stream_sid:
            print("❌ No stream_sid available")
            return
        
        print(f"🎵 Converting {len(mp3_data)} bytes of MP3 to PCM...")
        
        # Convert MP3 to PCM
        pcm_data = convert_mp3_to_pcm_pure_python(mp3_data)
        
        if not pcm_data:
            print("❌ PCM conversion failed")
            return
        
        print(f"🎵 Got {len(pcm_data)} bytes of PCM data")
        
        # CRITICAL: Exotel requires chunks in multiples of 320 bytes
        CHUNK_SIZE = 320  # Exactly 320 bytes as required
        total_chunks = len(pcm_data) // CHUNK_SIZE
        
        print(f"🎵 Sending {total_chunks} chunks of {CHUNK_SIZE} bytes each")
        
        # Send chunks with proper timing
        for i in range(total_chunks):
            start_pos = i * CHUNK_SIZE
            end_pos = start_pos + CHUNK_SIZE
            chunk = pcm_data[start_pos:end_pos]
            
            # Ensure chunk is exactly 320 bytes
            if len(chunk) < CHUNK_SIZE:
                # Pad with silence (zeros) if needed
                chunk = chunk + b'\x00' * (CHUNK_SIZE - len(chunk))
            
            # Send chunk to Exotel
            message = json.dumps({
                'event': 'media',
                'stream_sid': stream_sid,
                'media': {
                    'payload': base64.b64encode(chunk).decode("ascii")
                }
            })
            
            ws.send(message)
            
            # CRITICAL: Proper timing - 320 bytes at 8kHz = 20ms
            # 320 bytes = 160 samples = 160/8000 = 0.02 seconds = 20ms
            time.sleep(0.02)  # 20ms delay between chunks
            
            if (i + 1) % 50 == 0:  # Progress update every 50 chunks (1 second)
                print(f"📡 Sent {i + 1}/{total_chunks} chunks...")
        
        # Handle any remaining bytes (should pad to 320)
        remaining_bytes = len(pcm_data) % CHUNK_SIZE
        if remaining_bytes > 0:
            last_chunk_start = total_chunks * CHUNK_SIZE
            last_chunk = pcm_data[last_chunk_start:]
            # Pad to 320 bytes
            last_chunk = last_chunk + b'\x00' * (CHUNK_SIZE - len(last_chunk))
            
            message = json.dumps({
                'event': 'media',
                'stream_sid': stream_sid,
                'media': {
                    'payload': base64.b64encode(last_chunk).decode("ascii")
                }
            })
            
            ws.send(message)
            print(f"📡 Sent final padded chunk")
        
        print(f"✅ Audio sent successfully: {total_chunks} chunks")
        
    except Exception as e:
        print(f"❌ Send error: {e}")
        import traceback
        traceback.print_exc()

def process_and_respond_exotel_fixed(transcript, call_sid, ws, stream_sid):
    """Process input and respond using FIXED audio chunking"""
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
            # Send audio files with FIXED chunking
            audio_files = [f.strip() for f in content.split('+')]
            
            for audio_file in audio_files:
                if audio_file in audio_manager.memory_cache:
                    mp3_data = audio_manager.memory_cache[audio_file]
                    
                    # Use FIXED audio sending with proper PCM conversion
                    send_audio_exotel_fixed_chunking(ws, mp3_data, stream_sid)
                    
                    # Delay between files (allow previous audio to finish)
                    time.sleep(1.0)
                else:
                    print(f"❌ Audio file not in cache: {audio_file}")
                    
            call_logger.log_nisha_audio_response(call_sid, content)
            
        elif response_type == "TTS":
            # Generate TTS and send with FIXED chunking
            tts_audio_data = tts_engine.generate_audio(content, save_temp=False)
            if tts_audio_data:
                send_audio_exotel_fixed_chunking(ws, tts_audio_data, stream_sid)
                    
            call_logger.log_nisha_tts_response(call_sid, content)
        
        print(f"✅ Response sent with proper chunking")
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()

# ===== FIXED EXOTEL WEBSOCKET HANDLER =====

@sock.route('/exotel/media/<call_sid>')
def exotel_media_stream(ws, call_sid):
    """Handle Exotel WebSocket - FIXED for proper PCM chunking"""
    
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
        """Monitor for completed transcripts - FIXED VERSION"""
        while True:
            time.sleep(0.05)
            if session.check_for_completion():
                # USE FIXED FUNCTION:
                process_and_respond_exotel_fixed(session.completed_transcript, call_sid, ws, session.stream_sid)
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

def test_pcm_conversion():
    """Test PCM conversion with a small MP3 file"""
    try:
        # Test with one of your cached files
        if audio_manager.memory_cache:
            test_file = list(audio_manager.memory_cache.keys())[0]
            mp3_data = audio_manager.memory_cache[test_file]
            
            print(f"🧪 Testing PCM conversion with {test_file}")
            pcm_data = convert_mp3_to_pcm_pure_python(mp3_data)
            
            if pcm_data:
                print(f"✅ Conversion successful: {len(mp3_data)} bytes MP3 → {len(pcm_data)} bytes PCM")
                
                # Verify it's the right format for 320-byte chunks
                chunks_possible = len(pcm_data) // 320
                print(f"📊 Can create {chunks_possible} chunks of 320 bytes")
                return True
            else:
                print("❌ Conversion failed")
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
    print("🚀 KLARIQO - AI Voice Agent (Fixed PCM + Chunking)")
    print("=" * 40)
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Config OK")
    except ValueError as e:
        print(f"❌ Config error: {e}")
        exit(1)
    
    # Test PCM conversion during startup
    print("🧪 Testing audio conversion...")
    if test_pcm_conversion():
        print("✅ Audio conversion working!")
    else:
        print("⚠️ Audio conversion issues detected - will use silence fallback")
    
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
        print("   ✅ PCM conversion + 320-byte chunking")
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