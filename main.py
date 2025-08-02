import os
import json
import asyncio
import websockets
import base64
import subprocess
import tempfile
import shutil
from pathlib import Path
import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import threading
import requests
from openai import OpenAI
import time
import zipfile
import urllib.request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class PortableFFmpegManager:
    """
    Downloads and manages a portable FFmpeg installation
    No PATH modification needed!
    """
    
    def __init__(self):
        self.project_dir = os.getcwd()
        self.ffmpeg_dir = os.path.join(self.project_dir, "portable_ffmpeg")
        self.ffmpeg_exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
        
        # Try to get FFmpeg ready
        if not self._is_ffmpeg_ready():
            print("📦 Setting up portable FFmpeg...")
            self._setup_portable_ffmpeg()
    
    def _is_ffmpeg_ready(self):
        """Check if portable FFmpeg is ready to use"""
        if os.path.exists(self.ffmpeg_exe):
            try:
                # Test if it actually works
                result = subprocess.run([self.ffmpeg_exe, "-version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ Portable FFmpeg ready!")
                    return True
            except:
                pass
        return False
    
    def _setup_portable_ffmpeg(self):
        """Download and setup portable FFmpeg"""
        try:
            # Create directory
            os.makedirs(self.ffmpeg_dir, exist_ok=True)
            
            # Download URL for Windows 64-bit FFmpeg
            download_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            zip_path = os.path.join(self.ffmpeg_dir, "ffmpeg.zip")
            
            print("📥 Downloading FFmpeg (this may take a minute)...")
            self._download_with_progress(download_url, zip_path)
            
            print("📦 Extracting FFmpeg...")
            self._extract_ffmpeg(zip_path)
            
            # Cleanup
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            if self._is_ffmpeg_ready():
                print("✅ Portable FFmpeg setup complete!")
            else:
                raise Exception("FFmpeg setup verification failed")
        
        except Exception as e:
            print(f"❌ Failed to setup portable FFmpeg: {e}")
            print("🔧 Manual backup method:")
            print("1. Go to: https://github.com/BtbN/FFmpeg-Builds/releases")
            print("2. Download: ffmpeg-master-latest-win64-gpl.zip")
            print(f"3. Extract to: {self.ffmpeg_dir}")
            print("4. Make sure ffmpeg.exe is directly in the folder")
            raise
    
    def _download_with_progress(self, url, filepath):
        """Download file with progress indication"""
        try:
            def progress_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded * 100) // total_size)
                    if percent % 10 == 0:  # Show every 10%
                        print(f"📥 Downloaded: {percent}%")
            
            urllib.request.urlretrieve(url, filepath, progress_hook)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            raise
    
    def _extract_ffmpeg(self, zip_path):
        """Extract FFmpeg from downloaded zip"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find ffmpeg.exe in the zip
                ffmpeg_found = False
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('ffmpeg.exe'):
                        # Extract just the exe file
                        file_info.filename = 'ffmpeg.exe'  # Rename to simple name
                        zip_ref.extract(file_info, self.ffmpeg_dir)
                        ffmpeg_found = True
                        break
                
                if not ffmpeg_found:
                    raise Exception("ffmpeg.exe not found in downloaded archive")
        
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            raise
    
    def get_ffmpeg_path(self):
        """Get the path to the portable FFmpeg executable"""
        if self._is_ffmpeg_ready():
            return self.ffmpeg_exe
        else:
            raise RuntimeError("Portable FFmpeg not available")

class ExotelAudioConverter:
    """
    Audio converter using portable FFmpeg - NO INSTALLATION REQUIRED!
    """
    
    def __init__(self):
        try:
            self.ffmpeg_manager = PortableFFmpegManager()
            self.ffmpeg_path = self.ffmpeg_manager.get_ffmpeg_path()
            print("✅ Audio converter ready with portable FFmpeg")
        except Exception as e:
            print(f"❌ Audio converter failed: {e}")
            raise
    
    def convert_to_exotel_format(self, input_file_path):
        """
        Convert audio file to Exotel format: 16-bit, 8kHz, mono PCM
        """
        if not os.path.exists(input_file_path):
            print(f"❌ File not found: {input_file_path}")
            return None
        
        output_file_path = tempfile.mktemp(suffix='_exotel.wav')
        
        # FFmpeg command for Exotel format
        cmd = [
            self.ffmpeg_path,
            '-i', input_file_path,
            '-ar', '8000',          # Sample rate: 8kHz
            '-ac', '1',             # Channels: mono
            '-f', 'wav',            # Format: WAV
            '-acodec', 'pcm_s16le', # Codec: 16-bit PCM little-endian
            '-y',                   # Overwrite output
            output_file_path
        ]
        
        try:
            # Run FFmpeg with error capture
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=30
            )
            
            print(f"✅ Converted {os.path.basename(input_file_path)} to Exotel format")
            return output_file_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg conversion failed for {input_file_path}")
            print(f"   Error: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            print(f"❌ FFmpeg conversion timed out for {input_file_path}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error converting {input_file_path}: {str(e)}")
            return None
    
    def convert_to_base64(self, wav_file_path):
        """
        Convert WAV file to base64 for Exotel WebSocket
        """
        try:
            with open(wav_file_path, 'rb') as f:
                wav_data = f.read()
            
            # Skip WAV header (first 44 bytes) - Exotel wants raw PCM
            if len(wav_data) > 44:
                pcm_data = wav_data[44:]
            else:
                print(f"❌ WAV file too small: {wav_file_path}")
                return None
            
            # Encode to base64
            base64_data = base64.b64encode(pcm_data).decode('utf-8')
            return base64_data
            
        except Exception as e:
            print(f"❌ Base64 conversion failed for {wav_file_path}: {str(e)}")
            return None

# Fallback: Pure Python audio conversion (if even portable FFmpeg fails)
class FallbackAudioConverter:
    """
    Emergency fallback using pure Python libraries
    Much lower quality but works without any external dependencies
    """
    
    def __init__(self):
        try:
            import wave
            import struct
            print("⚠️ Using fallback audio converter (lower quality)")
        except ImportError:
            raise RuntimeError("No audio conversion method available")
    
    def convert_to_exotel_format(self, input_file_path):
        """
        Basic conversion - only works with WAV files
        """
        if not input_file_path.lower().endswith('.wav'):
            print(f"❌ Fallback converter only supports WAV files: {input_file_path}")
            return None
        
        try:
            import wave
            import struct
            
            output_file_path = tempfile.mktemp(suffix='_exotel_fallback.wav')
            
            # Read input WAV
            with wave.open(input_file_path, 'rb') as wav_in:
                frames = wav_in.readframes(wav_in.getnframes())
                sample_rate = wav_in.getframerate()
                channels = wav_in.getnchannels()
                sample_width = wav_in.getsampwidth()
            
            # Convert to 16-bit mono if needed (very basic)
            if sample_width != 2:  # Not 16-bit
                print(f"⚠️ Converting from {sample_width*8}-bit to 16-bit (basic conversion)")
            
            # Write output WAV at 8kHz mono 16-bit
            with wave.open(output_file_path, 'wb') as wav_out:
                wav_out.setnchannels(1)  # Mono
                wav_out.setsampwidth(2)  # 16-bit
                wav_out.setframerate(8000)  # 8kHz
                
                # Basic downsampling (very crude)
                if sample_rate != 8000:
                    step = sample_rate // 8000
                    frames = frames[::step * channels * sample_width]
                
                wav_out.writeframes(frames[:len(frames)//2])  # Crude mono conversion
            
            print(f"⚠️ Basic conversion completed: {os.path.basename(input_file_path)}")
            return output_file_path
        
        except Exception as e:
            print(f"❌ Fallback conversion failed: {e}")
            return None
    
    def convert_to_base64(self, wav_file_path):
        """Same base64 conversion as main converter"""
        try:
            with open(wav_file_path, 'rb') as f:
                wav_data = f.read()
            
            if len(wav_data) > 44:
                pcm_data = wav_data[44:]
                base64_data = base64.b64encode(pcm_data).decode('utf-8')
                return base64_data
            
            return None
        except Exception as e:
            print(f"❌ Fallback base64 conversion failed: {e}")
            return None

# Smart audio converter initialization
def initialize_audio_converter():
    """Initialize the best available audio converter"""
    try:
        # Try portable FFmpeg first
        return ExotelAudioConverter()
    except Exception as e:
        print(f"⚠️ Portable FFmpeg failed: {e}")
        try:
            # Fall back to basic Python converter
            return FallbackAudioConverter()
        except Exception as e2:
            print(f"❌ All audio conversion methods failed: {e2}")
            return None

# Initialize audio converter
audio_converter = initialize_audio_converter()

class ResponseRouter:
    """Handles response selection and audio conversion"""
    
    def __init__(self):
        self.audio_cache = self._load_audio_cache()
        if self.audio_cache:
            total_size = sum(item['size_mb'] for item in self.audio_cache.values())
            print(f"🎵 Audio cache: {len(self.audio_cache)} files loaded ({total_size:.1f}MB)")
    
    def _load_audio_cache(self):
        """Load available audio files"""
        cache = {}
        audio_dir = "audio_cache"
        
        if os.path.exists(audio_dir):
            for file in os.listdir(audio_dir):
                if file.endswith(('.mp3', '.wav')):
                    file_path = os.path.join(audio_dir, file)
                    file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                    cache[file] = {
                        'path': file_path,
                        'size_mb': round(file_size, 1)
                    }
        
        return cache
    
    def get_gpt_response_with_audio(self, user_input):
        """Get GPT response and select appropriate audio files"""
        try:
            # Your existing GPT logic here - simplified for example
            gpt_response = self._call_gpt(user_input)
            
            # Select audio files based on response
            audio_files = self._select_audio_files(gpt_response, user_input)
            
            return {
                'text': gpt_response,
                'audio_files': audio_files,
                'timestamp': time.time()
            }
        
        except Exception as e:
            print(f"❌ Error in GPT response: {e}")
            return {
                'text': "I apologize, there was an error processing your request.",
                'audio_files': [],
                'timestamp': time.time()
            }
    
    def _call_gpt(self, user_input):
        """Call GPT API"""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant for Klariqo. Respond in Hindi/English mix as appropriate."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"❌ GPT API error: {e}")
            return "मुझे खुशी होगी आपकी सहायता करने में। कृपया अपना सवाल दोबारा पूछें।"
    
    def _select_audio_files(self, gpt_response, user_input):
        """Select appropriate audio files based on response"""
        selected_files = []
        
        # Example selection logic based on keywords
        if "नमस्ते" in gpt_response or "स्वागत" in gpt_response:
            if "klariqo_provides_voice_agent1.mp3" in self.audio_cache:
                selected_files.append(self.audio_cache["klariqo_provides_voice_agent1.mp3"]['path'])
        
        if "voice agent" in gpt_response.lower() or "एजेंट" in gpt_response:
            if "voice_agents_trained_details.mp3" in self.audio_cache:
                selected_files.append(self.audio_cache["voice_agents_trained_details.mp3"]['path'])
        
        if "parents" in gpt_response.lower() or "माता-पिता" in gpt_response:
            if "basically_agent_answers_parents.mp3" in self.audio_cache:
                selected_files.append(self.audio_cache["basically_agent_answers_parents.mp3"]['path'])
        
        if "onboarding" in gpt_response.lower() or "गाइड" in gpt_response:
            if "agent_guides_onboarding_process.mp3" in self.audio_cache:
                selected_files.append(self.audio_cache["agent_guides_onboarding_process.mp3"]['path'])
        
        return selected_files
    
    def process_audio_for_exotel(self, audio_files):
        """Process audio files for Exotel transmission"""
        if not audio_converter:
            print("❌ No audio converter available")
            return []
        
        if not audio_files:
            print("⚠️ No audio files to process")
            return []
        
        all_chunks = []
        temp_files = []
        
        try:
            for audio_file in audio_files:
                # Convert to Exotel format
                exotel_wav = audio_converter.convert_to_exotel_format(audio_file)
                if not exotel_wav:
                    print(f"❌ Failed to convert {audio_file}")
                    continue
                
                temp_files.append(exotel_wav)
                
                # Convert to base64
                base64_data = audio_converter.convert_to_base64(exotel_wav)
                if not base64_data:
                    print(f"❌ Failed to encode {audio_file}")
                    continue
                
                # Split into chunks (multiple of 320 bytes as per Exotel requirement)
                chunks = self._chunk_base64_data(base64_data)
                all_chunks.extend(chunks)
                
                print(f"✅ Processed {os.path.basename(audio_file)} → {len(chunks)} chunks")
            
            return all_chunks
        
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def _chunk_base64_data(self, base64_data, chunk_size=3200):
        """Split base64 data into chunks for WebSocket transmission"""
        # Ensure chunk size is multiple of 320 (Exotel requirement)
        chunk_size = (chunk_size // 320) * 320
        
        # Convert back to bytes for proper chunking
        audio_bytes = base64.b64decode(base64_data)
        
        chunks = []
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            chunk_b64 = base64.b64encode(chunk).decode('utf-8')
            chunks.append(chunk_b64)
        
        return chunks

# Initialize response router
response_router = ResponseRouter()
if audio_converter:
    print("🤖 Response Router initialized: Audio conversion ready")
else:
    print("🤖 Response Router initialized: Text-only mode (no audio conversion)")

# WebSocket connections storage
active_connections = {}

@app.route('/exotel/voice', methods=['POST'])
def exotel_voice():
    """Handle incoming Exotel voice calls"""
    try:
        call_data = request.get_json() or {}
        
        # Generate WebSocket URL for this call
        call_sid = call_data.get('CallSid', 'unknown')
        websocket_url = f"{request.url_root.replace('http://', 'wss://').replace('https://', 'wss://')}exotel/media/{call_sid}"
        
        print(f"📞 Incoming call: {call_sid}")
        print(f"🔗 WebSocket: {websocket_url}")
        
        # Return VoiceBot response to Exotel
        response = {
            "Response": {
                "Say": "कनेक्ट हो रहे हैं...",
                "VoiceBot": {
                    "URL": websocket_url
                }
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"❌ Error in voice handler: {e}")
        return jsonify({"Response": {"Say": "तकनीकी समस्या है। कृपया बाद में कॉल करें।"}})

@app.route('/exotel/get_websocket', methods=['GET'])
def get_websocket():
    """Return WebSocket URL for Exotel"""
    try:
        # Get the base URL and convert to WebSocket
        base_url = request.url_root.replace('http://', 'wss://').replace('https://', 'wss://')
        websocket_url = f"{base_url}exotel/media/{{call_sid}}"
        
        return jsonify({
            "websocket_url": websocket_url,
            "status": "ready"
        })
    
    except Exception as e:
        print(f"❌ Error getting WebSocket URL: {e}")
        return jsonify({"error": str(e)}), 500

async def handle_exotel_websocket(websocket, path):
    """Handle WebSocket connections from Exotel"""
    try:
        # Extract call SID from path
        call_sid = path.split('/')[-1]
        active_connections[call_sid] = websocket
        
        print(f"🔌 Exotel connected: {call_sid}")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                await process_exotel_message(websocket, call_sid, data)
            
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from Exotel: {message}")
            except Exception as e:
                print(f"❌ Error processing message: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 Exotel disconnected: {call_sid}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        if call_sid in active_connections:
            del active_connections[call_sid]

async def process_exotel_message(websocket, call_sid, data):
    """Process messages from Exotel"""
    try:
        event = data.get('event')
        
        if event == 'connected':
            print(f"🔌 Exotel connected: {call_sid}")
        
        elif event == 'start':
            print(f"🎤 Stream started: {call_sid}")
            await send_initial_greeting(websocket)
        
        elif event == 'media':
            # Process incoming user audio
            media_data = data.get('media', {})
            audio_payload = media_data.get('payload', '')
            
            if audio_payload:
                await process_user_audio(websocket, call_sid, audio_payload)
        
        elif event == 'stop':
            print(f"🛑 Stream stopped: {call_sid}")
        
        elif event == 'dtmf':
            digit = data.get('dtmf', {}).get('digit', '')
            print(f"📞 DTMF received: {digit}")
    
    except Exception as e:
        print(f"❌ Error processing Exotel message: {e}")

async def send_initial_greeting(websocket):
    """Send initial greeting to caller"""
    try:
        # Get greeting response
        greeting_response = response_router.get_gpt_response_with_audio("बताइए?")
        
        # Process audio if converter is available
        if audio_converter and greeting_response['audio_files']:
            audio_chunks = response_router.process_audio_for_exotel(greeting_response['audio_files'])
            
            if audio_chunks:
                # Send audio chunks
                for i, chunk in enumerate(audio_chunks):
                    message = {
                        "event": "media",
                        "sequenceNumber": str(i + 1),
                        "media": {
                            "payload": chunk
                        }
                    }
                    await websocket.send(json.dumps(message))
                    await asyncio.sleep(0.01)
                
                # Send completion mark
                mark_message = {
                    "event": "mark",
                    "sequenceNumber": str(len(audio_chunks) + 1),
                    "mark": {"name": "greeting_complete"}
                }
                await websocket.send(json.dumps(mark_message))
                
                print(f"✅ Sent greeting: {len(audio_chunks)} chunks")
        else:
            # Text-only response if no audio converter
            print(f"🤖 AI: {greeting_response['text']} (text-only mode)")
        
    except Exception as e:
        print(f"❌ Error sending greeting: {e}")

async def process_user_audio(websocket, call_sid, audio_payload):
    """Process incoming user audio and respond"""
    try:
        # Simulate user said something
        user_text = "बताइए?"  # This would come from STT
        print(f"📞 User: {user_text}")
        
        # Get AI response
        response_data = response_router.get_gpt_response_with_audio(user_text)
        audio_files = response_data['audio_files']
        
        if audio_converter and audio_files:
            file_names = [os.path.basename(f) for f in audio_files]
            duration = len(audio_files) * 450  # Estimate
            print(f"🎯 GPT → Audio: {' + '.join(file_names)} ({duration}ms)")
            
            # Process and send audio
            audio_chunks = response_router.process_audio_for_exotel(audio_files)
            
            if audio_chunks:
                for i, chunk in enumerate(audio_chunks):
                    message = {
                        "event": "media",
                        "sequenceNumber": str(i + 1),
                        "media": {
                            "payload": chunk
                        }
                    }
                    await websocket.send(json.dumps(message))
                    await asyncio.sleep(0.01)
                
                print(f"✅ Response sent")
            else:
                print(f"❌ Failed to convert audio files")
        else:
            print(f"🤖 AI: {response_data['text']} (text-only mode)")
    
    except Exception as e:
        print(f"❌ Error processing user audio: {e}")

def start_websocket_server():
    """Start WebSocket server for Exotel"""
    try:
        import asyncio
        import websockets
        
        # Start WebSocket server
        start_server = websockets.serve(
            handle_exotel_websocket,
            "0.0.0.0",
            8765
        )
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    
    except Exception as e:
        print(f"❌ WebSocket server error: {e}")

def main():
    """Main function to start the application"""
    try:
        # Check configuration
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ OPENAI_API_KEY not found in environment variables")
            return
        
        print("✅ Config OK")
        
        # Start ngrok for public access
        print("🚀 Starting ngrok...")
        try:
            import subprocess
            ngrok_process = subprocess.Popen(['ngrok', 'http', '5000'], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE)
            time.sleep(3)  # Wait for ngrok to start
            
            # Get ngrok URL (you'll need to replace this with actual detection)
            ngrok_url = "https://your-ngrok-url.ngrok-free.app"
            print(f"🌐 Public URL: {ngrok_url}")
            print(f"📞 EXOTEL SETUP:")
            print(f"   Incoming Call URL: {ngrok_url}/exotel/voice")
            print(f"   Voicebot URL: {ngrok_url}/exotel/get_websocket")
        
        except:
            print("⚠️ Ngrok not available - using local URLs")
            ngrok_url = "http://localhost:5000"
        
        print("🔧 EXOTEL FLOW:")
        print("   Greeting → Voicebot")
        print("   ✅ YES, that's correct!")
        print("✅ READY!")
        print("=" * 40)
        
        # Start WebSocket server in a separate thread
        websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
        websocket_thread.start()
        
        # Start Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main()