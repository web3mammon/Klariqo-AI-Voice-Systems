#!/usr/bin/env python3
"""
AVS INTERNATIONAL SCHOOL INBOUND CALL ROUTES
Handles incoming calls from parents inquiring about admissions
"""

import os
import sys
import random

# Fix import path for parent directory modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

from session import session_manager
from logger import call_logger
from audio_manager import audio_manager

# Create blueprint for inbound routes
inbound_bp = Blueprint('inbound', __name__)

@inbound_bp.route("/twilio/voice", methods=['POST'])
def handle_incoming_call():
    """Handle INBOUND calls from prospects"""
    
    # Extract call information
    caller = request.form.get('From', 'Unknown')
    call_sid = request.form.get('CallSid', 'unknown')
    
    print(f"📞 INBOUND call from parent: {caller}")
    
    # Log call start
    call_logger.log_call_start(call_sid, caller, "inbound")
    
    # Create INBOUND session for parent inquiry
    session = session_manager.create_session(call_sid, call_direction="inbound")
    
    # Build TwiML response
    response = VoiceResponse()
    
    # Use school intro for parent calls
    selected_intro = "school_intro.mp3"
    
    # Mark intro as played in session memory
    session.session_memory["intro_played"] = True
    
    # Play intro audio
    intro_url = f"{request.url_root}audio_pcm/{selected_intro}"
    response.play(intro_url)
    
    # Log the intro response
    call_logger.log_nisha_audio_response(call_sid, selected_intro)
    
    # Connect to WebSocket for real-time streaming
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media/{call_sid}')
    connect.append(stream)
    response.append(connect)
    
    return str(response)

@inbound_bp.route("/twilio/continue/<call_sid>", methods=['POST'])
def continue_inbound_conversation(call_sid):
    """Continue inbound conversation after processing user input"""
    
    try:
        session = session_manager.get_session(call_sid)
        if not session or not hasattr(session, 'ready_for_twiml'):
            print(f"❌ No session or not ready: {call_sid}")
            response = VoiceResponse()
            response.say("Processing error")
            response.hangup()
            return str(response)
        
        # Get prepared response
        response_type = session.next_response_type
        content = session.next_response_content
        transcript = session.next_transcript
        
        # Add to conversation history
        session.add_to_history("Parent", transcript)
        session.add_to_history("Nisha", content)
        
        # Build TwiML response
        twiml_response = VoiceResponse()
        
        if response_type == "AUDIO":
            # Handle audio file response
            audio_files = [f.strip() for f in content.split('+')]
            
            # Validate all files exist
            if audio_manager.validate_audio_chain(content):
                for audio_file in audio_files:
                    audio_url = f"{request.url_root}audio_pcm/{audio_file}"
                    twiml_response.play(audio_url)
                
                # Log audio response
                call_logger.log_nisha_audio_response(call_sid, content)
            else:
                # Fallback if files don't exist
                twiml_response.say("I'm having trouble with my audio files.")
                call_logger.log_nisha_tts_response(call_sid, "Audio file error - fallback")
        
        elif response_type == "TTS":
            # Handle TTS response
            from tts_engine import tts_engine
            
            tts_url = tts_engine.generate_audio_url(content, request.url_root)
            if tts_url:
                twiml_response.play(tts_url)
                call_logger.log_nisha_tts_response(call_sid, content)
            else:
                twiml_response.say("Sorry, I'm having trouble generating audio.")
                call_logger.log_nisha_tts_response(call_sid, "TTS generation failed")
        
        # Check if conversation should end
        if any(word in content.lower() for word in ["goodbye", "goodbye1.mp3"]):
            twiml_response.hangup()
            
            # Clean up session
            call_logger.log_call_end(call_sid, "completed")
            session_manager.remove_session(call_sid)
            
        else:
            # Reset session for next input
            session.reset_for_next_input()
            
            # Continue streaming
            connect = Connect()
            stream = Stream(url=f'wss://{request.host}/media/{call_sid}')
            connect.append(stream)
            twiml_response.append(connect)
        
        return str(twiml_response)
        
    except Exception as e:
        print(f"❌ Error in inbound continue: {e}")
        
        # Log error and cleanup
        call_logger.log_call_end(call_sid, "error")
        session_manager.remove_session(call_sid)
        
        response = VoiceResponse()
        response.say("I'm having technical difficulties.")
        response.hangup()
        return str(response)