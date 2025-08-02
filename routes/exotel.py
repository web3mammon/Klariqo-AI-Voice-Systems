#!/usr/bin/env python3
"""
FIXED EXOTEL ROUTES MODULE
Handles Exotel WebStreaming for incoming calls with CORRECT implementation
"""

import random
import time
import json
import base64
import audioop
from flask import Blueprint, request, Response
from session import session_manager
from router import response_router  # Using your main router
from audio_manager import audio_manager
from logger import call_logger
from tts_engine import tts_engine

exotel_bp = Blueprint('exotel', __name__)

@exotel_bp.route("/exotel/voice", methods=['POST'])
def handle_exotel_incoming():
    """Handle incoming call from Exotel with CORRECT XML format"""
    
    # Get call details from Exotel webhook
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"📞 Exotel Incoming Call:")
    print(f"   Call SID: {call_sid}")
    print(f"   From: {from_number}")
    print(f"   To: {to_number}")
    
    # Create session for this call
    session = session_manager.create_session(call_sid, "inbound")
    session.session_memory["intro_played"] = True
    
    # Log call start
    call_logger.log_call_start(call_sid, from_number, "inbound")
    
    # Select random intro file
    intro_files = [f for f in audio_manager.cached_files if f.startswith('intro_klariqo')]
    selected_intro = random.choice(intro_files) if intro_files else "intro_klariqo.mp3"
    
    # Get base URL for serving files
    base_url = request.url_root.rstrip('/')
    intro_url = f"{base_url}/audio_optimised/{selected_intro}"
    
    # CRITICAL: Use dynamic CallSid in WebSocket URL
    webstream_url = f"wss://{request.host}/exotel/media/{call_sid}"
    
    print(f"🎵 Playing intro: {intro_url}")
    print(f"🔌 WebSocket URL: {webstream_url}")
    
    # FIXED: Use correct Exotel XML format (NOT TwiML)
    exotel_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{intro_url}</Play>
    <Voicebot url="{webstream_url}" />
</Response>"""
    
    # Log the intro response
    call_logger.log_nisha_audio_response(call_sid, selected_intro)
    
    return exotel_response, 200, {'Content-Type': 'application/xml'}

@exotel_bp.route("/exotel/continue/<call_sid>", methods=['POST', 'GET'])  
def continue_exotel_call(call_sid):
    """Continue Exotel call after Voicebot applet ends (Passthru webhook)"""
    
    session = session_manager.get_session(call_sid)
    if not session:
        print(f"❌ No session found for {call_sid}")
        return "Session not found", 404
    
    # Get Exotel passthru parameters
    stream_sid = request.form.get('StreamSid') or request.args.get('StreamSid')
    disconnected_by = request.form.get('DisconnectedBy') or request.args.get('DisconnectedBy')
    
    print(f"📞 Exotel Passthru: {call_sid}")
    print(f"   StreamSid: {stream_sid}")
    print(f"   DisconnectedBy: {disconnected_by}")
    
    # Check if we have a prepared response
    if hasattr(session, 'ready_for_twiml') and session.ready_for_twiml:
        
        response_type = session.next_response_type
        content = session.next_response_content
        
        # Get base URL for serving files
        base_url = request.url_root.rstrip('/')
        webstream_url = f"wss://{request.host}/exotel/media/{call_sid}"
        
        if response_type == "AUDIO":
            # Chain multiple audio files
            audio_files = [f.strip() for f in content.split('+')]
            play_elements = []
            
            for audio_file in audio_files:
                audio_url = f"{base_url}/audio_optimised/{audio_file}"
                play_elements.append(f"<Play>{audio_url}</Play>")
            
            # Log the response
            call_logger.log_nisha_audio_response(call_sid, content)
            
            # FIXED: Use correct Exotel XML format
            exotel_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {''.join(play_elements)}
    <Voicebot url="{webstream_url}" />
</Response>"""
            
        elif response_type == "TTS":
            # Generate TTS URL
            tts_url = tts_engine.generate_audio_url(content, base_url)
            
            if tts_url:
                # Log the TTS response
                call_logger.log_nisha_tts_response(call_sid, content)
                
                exotel_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{tts_url}</Play>
    <Voicebot url="{webstream_url}" />
</Response>"""
            else:
                exotel_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, I'm having trouble generating audio.</Say>
    <Hangup />
</Response>"""
        
        # Reset session state
        session.reset_for_next_input()
        
        return exotel_response, 200, {'Content-Type': 'application/xml'}
    
    else:
        # No response ready - end call or provide fallback
        print(f"❌ No response ready for {call_sid}")
        
        fallback_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thank you for your time. Goodbye!</Say>
    <Hangup />
</Response>"""
        
        # Log call end
        call_logger.log_call_end(call_sid, "completed")
        session_manager.remove_session(call_sid)
        
        return fallback_response, 200, {'Content-Type': 'application/xml'}

@exotel_bp.route("/exotel/status", methods=['POST'])
def exotel_call_status():
    """Handle Exotel call status updates"""
    
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    print(f"📞 Exotel Status Update: {call_sid} → {call_status}")
    
    if call_status in ['completed', 'failed', 'busy', 'no-answer']:
        # Log call end
        call_logger.log_call_end(call_sid, call_status)
        
        # Clean up session
        session_manager.remove_session(call_sid)
    
    return "OK", 200

# FIXED WebSocket handler for Exotel-specific event format
def handle_exotel_websocket(ws, call_sid):
    """Handle Exotel WebSocket streaming with CORRECT event handling"""
    
    session = session_manager.get_session(call_sid)
    if not session:
        print(f"❌ No session found for Exotel call {call_sid}")
        return
    
    session.twilio_ws = ws  # Reuse same WebSocket reference
    
    def start_deepgram():
        """Initialize Deepgram connection for Exotel session"""
        try:
            from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
            from config import Config
            
            config = DeepgramClientOptions(options={"keepalive": "true"})
            deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY, config)
            
            options = LiveOptions(
                model=Config.DEEPGRAM_MODEL,
                language=Config.DEEPGRAM_LANGUAGE,
                punctuate=True,
                smart_format=True,
                sample_rate=8000,  # Exotel uses 8kHz
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
            print(f"❌ Deepgram setup error for Exotel: {e}")
    
    # Start Deepgram in separate thread
    import threading
    deepgram_thread = threading.Thread(target=start_deepgram)
    deepgram_thread.daemon = True
    deepgram_thread.start()
    time.sleep(0.5)  # Give Deepgram time to connect
    
    def transcript_checker():
        """Monitor for completed transcripts"""
        while True:
            time.sleep(0.05)  # Check every 50ms
            if session.check_for_completion():
                process_exotel_user_input(session.completed_transcript, call_sid)
                break
    
    # Start transcript checker
    checker_thread = threading.Thread(target=transcript_checker)
    checker_thread.daemon = True
    checker_thread.start()
    
    try:
        # Handle WebSocket messages from Exotel
        while True:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            event_type = data.get('event')
            
            # FIXED: Handle Exotel-specific event types
            if event_type == 'connected':
                print(f"🔌 Exotel WebSocket connected: {call_sid}")
                
            elif event_type == 'start':
                print(f"🎤 Exotel streaming started: {call_sid}")
                
            elif event_type == 'media':
                # Forward audio to Deepgram
                if session.dg_connection:
                    media_payload = data.get('media', {}).get('payload')
                    if media_payload:
                        try:
                            # FIXED: Exotel sends Linear PCM, not μ-law like Twilio
                            # Exotel format: base64-encoded Linear PCM (16-bit, 8kHz, mono)
                            linear_data = base64.b64decode(media_payload)
                            session.dg_connection.send(linear_data)
                        except Exception as e:
                            print(f"⚠️ Exotel audio processing error: {e}")
                            
            elif event_type == 'stop':
                print(f"🛑 Exotel streaming stopped: {call_sid}")
                break
                
            elif event_type == 'dtmf':
                # Handle DTMF if needed
                digit = data.get('dtmf', {}).get('digit')
                print(f"📞 DTMF received: {digit}")
                
    except Exception as e:
        print(f"❌ Exotel WebSocket error for {call_sid}: {e}")
        
    finally:
        # Cleanup session
        if session.dg_connection:
            session.dg_connection.finish()
            session.dg_connection = None
        print(f"🧹 Cleaned up Exotel session: {call_sid}")

def process_exotel_user_input(transcript, call_sid):
    """Process user input for Exotel calls"""
    try:
        session = session_manager.get_session(call_sid)
        if not session:
            return
        
        start_time = time.time()
        
        # Log principal's input
        call_logger.log_principal_input(call_sid, transcript)
        
        # Get AI response using your existing router
        response_type, content = response_router.get_school_response(transcript, session)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Generate TTS if needed (BEFORE preparing response)
        if response_type == "TTS":
            temp_filename = tts_engine.generate_audio(content, save_temp=True)
            if not temp_filename:
                print(f"❌ TTS generation failed for: {content}")
                return
            else:
                print(f"✅ TTS generated: {temp_filename}")
        
        # Prepare session for response
        session.next_response_type = response_type
        session.next_response_content = content
        session.next_transcript = transcript
        session.ready_for_twiml = True
        
        # Add to conversation history
        session.add_to_history("Principal", transcript)
        session.add_to_history("Nisha", f"<{response_type}: {content}>")
        
        # Clean logging
        print(f"📞 User: {transcript}")
        if response_type == "AUDIO":
            print(f"📞 AI Response: {content} ({response_time_ms}ms)")
        else:
            print(f"📞 TTS Response: {content} ({response_time_ms}ms)")
        
        # The session is now ready - Exotel will call /exotel/continue when Voicebot ends
        
    except Exception as e:
        print(f"❌ Exotel processing error for {call_sid}: {e}")

@exotel_bp.route("/exotel/debug", methods=['GET'])
def exotel_debug():
    """Debug endpoint to check Exotel setup"""
    
    return {
        "status": "Exotel WebStreaming Ready",
        "active_sessions": session_manager.get_active_count(),
        "cached_audio_files": len(audio_manager.cached_files),
        "endpoints": {
            "incoming": "/exotel/voice",
            "continue": "/exotel/continue/<call_sid>",
            "status": "/exotel/status",
            "websocket": "/exotel/media/<call_sid>"
        },
        "fixes_applied": [
            "✅ Correct Exotel XML format (Voicebot vs StartWebStream)",
            "✅ Proper Exotel WebSocket event handling",
            "✅ Linear PCM audio processing (not μ-law)",
            "✅ Dynamic CallSid in WebSocket URLs",
            "✅ Passthru applet integration"
        ]
    }