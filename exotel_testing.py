#!/usr/bin/env python3
"""
EXOTEL DEBUG SCRIPT - Shows exactly what's happening
"""

import os
import json
import time 
import base64
import threading
import subprocess
import urllib.request
from flask import Flask, request
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

# Silence Flask logs
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

sessions = {}

@app.route("/exotel/voice", methods=['POST'])
def incoming_call():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From', 'Unknown')
    
    print(f"\n📞 INCOMING CALL")
    print(f"   CallSid: {call_sid}")
    print(f"   From: {from_number}")
    print(f"   All form data: {dict(request.form)}")
    
    sessions[call_sid] = {'start_time': time.time()}
    
    websocket_url = f"https://{request.host}/exotel/get_websocket"
    
    response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Debug test. Please say something after the beep.</Say>
    <Voicebot url="{websocket_url}" />
</Response>"""
    
    print(f"📤 SENT TO EXOTEL:")
    print(response)
    
    return response, 200, {'Content-Type': 'application/xml'}

@app.route("/exotel/get_websocket", methods=['GET'])
def get_websocket():
    call_sid = request.args.get('CallSid')
    
    print(f"\n🔗 WEBSOCKET REQUEST")
    print(f"   CallSid: {call_sid}")
    print(f"   All args: {dict(request.args)}")
    
    if not call_sid:
        print("❌ No CallSid in request!")
        return {"error": "Missing CallSid"}, 400
    
    websocket_url = f"wss://{request.host}/exotel/media/{call_sid}"
    
    response = {"url": websocket_url}
    print(f"📤 WEBSOCKET RESPONSE: {response}")
    
    return response, 200

@sock.route('/exotel/media/<call_sid>')
def websocket_handler(ws, call_sid):
    print(f"\n🔌 WEBSOCKET CONNECTED: {call_sid}")
    
    session = sessions.get(call_sid, {})
    session['websocket_connected'] = True
    session['messages_received'] = 0
    session['media_count'] = 0
    session['stream_sid'] = None
    
    try:
        while True:
            message = ws.receive()
            if not message:
                print("❌ No message received - connection closed")
                break
                
            session['messages_received'] += 1
            
            try:
                data = json.loads(message)
                event = data.get('event', 'UNKNOWN')
                
                print(f"\n📨 MESSAGE #{session['messages_received']}: {event}")
                print(f"   Full data: {json.dumps(data, indent=2)}")
                
                if event == 'connected':
                    print("✅ CONNECTED event received")
                    
                elif event == 'start':
                    session['stream_sid'] = data.get('stream_sid')
                    print(f"✅ START event - StreamSid: {session['stream_sid']}")
                    
                elif event == 'media':
                    session['media_count'] += 1
                    media_data = data.get('media', {})
                    payload = media_data.get('payload', '')
                    
                    print(f"🎵 MEDIA #{session['media_count']} - Payload length: {len(payload)}")
                    
                    # After receiving some media, send test audio back
                    if session['media_count'] == 5:  # Send after 5 media packets
                        print("\n🔊 SENDING TEST AUDIO...")
                        send_test_audio(ws, session['stream_sid'])
                    
                elif event == 'stop':
                    print("🛑 STOP event received")
                    break
                    
                elif event == 'dtmf':
                    digit = data.get('dtmf', {}).get('digit', '')
                    print(f"📞 DTMF: {digit}")
                    
                else:
                    print(f"❓ UNKNOWN EVENT: {event}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"   Raw message: {message[:200]}...")
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        
    finally:
        print(f"\n🔚 WEBSOCKET CLOSED")
        print(f"   Total messages: {session['messages_received']}")
        print(f"   Media packets: {session['media_count']}")
        print(f"   StreamSid: {session.get('stream_sid', 'None')}")

def send_test_audio(ws, stream_sid):
    """Send test audio to Exotel"""
    
    if not stream_sid:
        print("❌ No stream_sid - cannot send audio")
        return
    
    print(f"🎵 Preparing test audio for stream_sid: {stream_sid}")
    
    # Create test audio - 1 second of 440Hz tone (A note)
    import math
    sample_rate = 8000
    duration = 1.0  # 1 second
    frequency = 440  # A note
    
    audio_data = bytearray()
    for i in range(int(sample_rate * duration)):
        # Generate sine wave
        sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        # Convert to 16-bit little-endian
        audio_data.extend(sample.to_bytes(2, 'little', signed=True))
    
    print(f"🎵 Generated {len(audio_data)} bytes of test audio")
    
    # Send in chunks exactly as Exotel expects
    chunk_size = 320  # Exotel requires multiples of 320 bytes
    total_chunks = len(audio_data) // chunk_size
    
    print(f"🔊 Sending {total_chunks} chunks of {chunk_size} bytes each")
    
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i + chunk_size]
        
        # Pad chunk if needed
        if len(chunk) < chunk_size:
            chunk.extend(b'\x00' * (chunk_size - len(chunk)))
        
        # Create message in Exotel format
        message = {
            'event': 'media',
            'stream_sid': stream_sid,
            'media': {
                'payload': base64.b64encode(chunk).decode('ascii')
            }
        }
        
        try:
            ws.send(json.dumps(message))
            print(f"📤 Sent chunk {i//chunk_size + 1}/{total_chunks}")
            time.sleep(0.02)  # 20ms delay between chunks
            
        except Exception as e:
            print(f"❌ Error sending chunk {i//chunk_size + 1}: {e}")
            break
    
    print("✅ Test audio sent!")
    
    # Send mark to indicate completion
    mark_message = {
        'event': 'mark',
        'stream_sid': stream_sid,
        'mark': {
            'name': 'test_audio_complete'
        }
    }
    
    try:
        ws.send(json.dumps(mark_message))
        print("✅ Mark sent")
    except Exception as e:
        print(f"❌ Error sending mark: {e}")

def start_ngrok():
    """Start ngrok and get public URL"""
    try:
        # Check if already running
        try:
            with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
                data = json.loads(response.read())
                for tunnel in data['tunnels']:
                    if tunnel.get('proto') == 'https':
                        return tunnel['public_url']
        except:
            pass
        
        # Start ngrok
        print("🚀 Starting ngrok...")
        subprocess.Popen(['ngrok', 'http', '5000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        
        # Get URL
        for attempt in range(10):
            try:
                with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
                    data = json.loads(response.read())
                    for tunnel in data['tunnels']:
                        if tunnel.get('proto') == 'https':
                            return tunnel['public_url']
                time.sleep(1)
            except:
                time.sleep(1)
        
        return None
    except:
        return None

if __name__ == "__main__":
    print("🐛 EXOTEL DEBUG SCRIPT")
    print("=" * 50)
    print("This will show EXACTLY what Exotel sends/receives")
    print("=" * 50)
    
    # Start ngrok
    ngrok_url = start_ngrok()
    
    if ngrok_url:
        print(f"\n🌐 NGROK URL: {ngrok_url}")
        print(f"📞 EXOTEL INCOMING URL: {ngrok_url}/exotel/voice")
        print("\n🔧 EXOTEL SETUP:")
        print("1. Add Voicebot applet to your Exotel flow")
        print(f"2. Set URL to: {ngrok_url}/exotel/voice")
        print("3. Call your Exotel number")
        print("4. Watch this console for detailed debug info")
        print("\n✅ Ready for debugging!")
    else:
        print("❌ ngrok failed")
        exit(1)
    
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)