#!/usr/bin/env python3
"""
KLARIQO OUTBOUND CALL ROUTES  
Handles outbound calls to schools and prospects
"""

import os
import sys
import threading
import time

# Fix import path for parent directory modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.rest import Client

from config import Config
from session import session_manager
from logger import call_logger

# Create blueprint for outbound routes
outbound_bp = Blueprint('outbound', __name__)

# Initialize Twilio client
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

@outbound_bp.route("/twilio/outbound/<lead_id>", methods=['GET', 'POST'])
def handle_outbound_call(lead_id):
    """Handle OUTBOUND calls to schools/prospects"""
    
    # Extract call information (handle both GET and POST)
    call_sid = request.form.get('CallSid') or request.args.get('CallSid', 'unknown')
    to_number = request.form.get('To') or request.args.get('To', 'Unknown')
    from_number = request.form.get('From') or request.args.get('From', 'Unknown')
    
    print(f"🔍 DEBUG: Method={request.method}")
    print(f"🔍 DEBUG: CallSid={call_sid}")
    print(f"🔍 DEBUG: To={to_number}, From={from_number}")
    
    # Get lead data (in real implementation, fetch from database)
    lead_data = {
        'id': lead_id, 
        'school_name': 'Test School Demo', 
        'type': 'school',
        'phone': to_number
    }
    
    print(f"🏫 OUTBOUND call connected to {lead_data['school_name']}")
    
    # Log call start
    call_logger.log_call_start(call_sid, lead_data['phone'], "outbound", lead_data)
    
    # Create OUTBOUND session
    session = session_manager.create_session(
        call_sid, 
        call_direction="outbound", 
        lead_data=lead_data
    )
    
    # Build TwiML response
    response = VoiceResponse()
    
    # Use consistent intro for outbound (sales mode)
    selected_intro = "intro_klariqo.mp3"
    session.session_memory["intro_played"] = True
    
    # Play intro audio
    intro_url = f"{request.url_root}audio_optimised/{selected_intro}"
    print(f"🎵 Playing intro: {intro_url}")
    response.play(intro_url)
    
    # Log the intro response
    call_logger.log_nisha_audio_response(call_sid, selected_intro)
    
    # Connect to WebSocket for real-time streaming
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media/{call_sid}')
    connect.append(stream)
    response.append(connect)
    
    print(f"📞 TwiML Response: {str(response)}")
    return str(response)

@outbound_bp.route("/twilio/continue/<call_sid>", methods=['POST'])
def continue_outbound_conversation(call_sid):
    """Continue outbound conversation after processing user input"""
    
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
        session.add_to_history("Principal", transcript)
        session.add_to_history("Nisha", content)
        
        # Build TwiML response
        twiml_response = VoiceResponse()
        
        if response_type == "AUDIO":
            # Handle audio file response
            from audio_manager import audio_manager
            
            audio_files = [f.strip() for f in content.split('+')]
            
            # Validate all files exist
            if audio_manager.validate_audio_chain(content):
                for audio_file in audio_files:
                    audio_url = f"{request.url_root}audio_optimised/{audio_file}"
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
        print(f"❌ Error in outbound continue: {e}")
        
        # Log error and cleanup
        call_logger.log_call_end(call_sid, "error")
        session_manager.remove_session(call_sid)
        
        response = VoiceResponse()
        response.say("I'm having technical difficulties.")
        response.hangup()
        return str(response)

def make_outbound_call(target_number, lead_data, base_url):
    """Make an outbound call to a school/prospect"""
    try:
        # Ensure phone number has + prefix
        if not target_number.startswith('+'):
            target_number = '+' + target_number
            
        print(f"📞 Calling {lead_data.get('school_name')} at {target_number}")
        
        call = twilio_client.calls.create(
            to=target_number,
            from_=Config.TWILIO_PHONE,
            url=f"{base_url}/outbound/twilio/outbound/{lead_data['id']}",
            method='POST'
        )
        
        # Track call info
        session_manager.track_outbound_call(call.sid, lead_data)
        
        print(f"✅ Outbound call initiated: {call.sid}")
        print(f"📋 Webhook URL: {base_url}/outbound/twilio/outbound/{lead_data['id']}")
        return call.sid
        
    except Exception as e:
        print(f"❌ Failed to make outbound call: {e}")
        return None

def start_school_calling_campaign(target_list, max_calls=50, base_url=""):
    """Start mass outbound calling campaign to schools"""
    
    call_count = 0
    successful_calls = 0
    
    for school in target_list:
        if call_count >= max_calls:
            break
            
        # Check if already called today (in real implementation)
        if not school.get('called_today', False):
            call_sid = make_outbound_call(school['phone'], school, base_url)
            
            if call_sid:
                successful_calls += 1
                # Wait between calls (be respectful!)
                time.sleep(Config.CALL_INTERVAL)
                
            call_count += 1
                
        if call_count >= max_calls:
            break
    
    print(f"🚀 School campaign complete: {successful_calls}/{call_count} calls successful")
    return successful_calls

@outbound_bp.route("/start_campaign", methods=['POST'])
def start_campaign():
    """API endpoint to start school calling campaign"""
    try:
        # Sample school data (in real implementation, load from database/CSV)
        sample_schools = [
            {
                'id': '1', 
                'school_name': 'DPS School Delhi', 
                'phone': '+91XXXXXXXXXX', 
                'type': 'school'
            },
            {
                'id': '2', 
                'school_name': 'Ryan International', 
                'phone': '+91XXXXXXXXXX', 
                'type': 'school'
            },
            # Add more schools from your database...
        ]
        
        # Get base URL for callbacks
        base_url = request.url_root.rstrip('/')
        
        # Start campaign in background thread
        campaign_thread = threading.Thread(
            target=start_school_calling_campaign, 
            args=(sample_schools, 10, base_url)  # Start with 10 calls
        )
        campaign_thread.daemon = True
        campaign_thread.start()
        
        return {
            "status": "success", 
            "message": "School campaign started",
            "max_calls": 10
        }
        
    except Exception as e:
        print(f"❌ Campaign start error: {e}")
        return {
            "status": "error", 
            "message": str(e)
        }

@outbound_bp.route("/campaign_status", methods=['GET'])
def get_campaign_status():
    """Get current campaign status"""
    active_count = session_manager.get_active_count()
    
    # Get recent call stats
    stats = call_logger.get_call_stats(days=1)
    
    return {
        "active_calls": active_count,
        "today_stats": stats,
        "outbound_calls_tracked": len(session_manager.active_outbound_calls)
    }