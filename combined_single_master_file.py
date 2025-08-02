#!/usr/bin/env python3
"""
KLARIQO SCHOOL OUTBOUND SYSTEM
Handles both inbound AND outbound calls on same number
Perfect for school sales campaigns + demos
Based on original hotel streaming architecture
"""

import os
import json
import time
import asyncio
import base64
import requests
import threading
import audioop
import pandas as pd
from datetime import datetime
from flask import Flask, request, send_file, redirect, url_for
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.rest import Client
from groq import Groq
from elevenlabs import ElevenLabs, VoiceSettings
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions, 
    LiveTranscriptionEvents,
    LiveOptions,
)

# API Keys
DEEPGRAM_API_KEY = "eb1d2caf340731b7ae359375a2fb67f45be97935"
GROQ_API_KEY = "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"
ELEVENLABS_API_KEY = "sk_08182ff24f343352bd9b84d1e1253b6906551ab95775001a"
TWILIO_ACCOUNT_SID = "AC9ed859c2ccb77aa9d3feb59b5813bb9c"
TWILIO_AUTH_TOKEN = "4ee3690aa04ba34f52edb7ea3c687c2a"
TWILIO_PHONE = "+19123781882"

# Initialize services
groq_client = Groq(api_key=GROQ_API_KEY)
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
VOICE_ID = "TRnaQb7q41oL7sV0w6Bu"

# Initialize Deepgram
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)

# Flask app with WebSocket support
app = Flask(__name__)
sock = Sock(app)

# Session memory for school conversations
session_flags = {
    "intro_played": False,
    "klariqo_explained": False,
    "features_discussed": False,
    "pricing_mentioned": False,
    "demo_offered": False,
    "meeting_scheduled": False
}

class StreamingSession:
    def __init__(self, call_sid, call_direction="inbound", lead_data=None):
        self.call_sid = call_sid
        self.call_direction = call_direction  # "inbound" or "outbound"
        self.lead_data = lead_data or {}  # School info for outbound
        self.session_memory = session_flags.copy()
        self.conversation_history = []
        self.accumulated_text = ""
        self.last_activity_time = None
        self.silence_threshold = 0.4
        self.is_processing = False
        self.dg_connection = None
        self.twilio_ws = None
        self.completed_transcript = None
        self.transcript_ready = False
    
    def on_deepgram_open(self, *args, **kwargs):
        pass
    
    def on_deepgram_message(self, *args, **kwargs):
        if self.is_processing:
            return
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
        pass
    
    def check_for_completion(self):
        if (self.accumulated_text and 
            self.last_activity_time and 
            time.time() - self.last_activity_time >= self.silence_threshold and
            not self.is_processing):
            self.completed_transcript = self.accumulated_text
            self.transcript_ready = True
            self.accumulated_text = ""
            self.last_activity_time = None
            return True
        return False
    
    def cleanup(self):
        try:
            if self.dg_connection:
                self.dg_connection.finish()
        except:
            pass

# Active sessions (supports concurrent calls!)
active_sessions = {}

# Response cache for common school queries
response_cache = {
    "klariqo क्या है": "klariqo_provides_voice_agent1.mp3",
    "what is klariqo": "klariqo_provides_voice_agent1.mp3",
    "voice agent": "voice_agents_trained_details.mp3",
    "24/7": "agents_need_no_breaks.mp3",
    "concurrent calls": "klariqo_concurrent_calls.mp3",
    "realistic": "klariqo_agents_sound_so_realistic.mp3",
    "pricing": "klariqo_pricing1.1.mp3",
    "cost": "klariqo_pricing1.1.mp3",
    "15000": "klariqo_pricing1.1.mp3",
    "demo": "glad_for_demo_and_patent_mention1.1.mp3",
    "meeting": "meeting_with_founder.mp3",
    "founder": "why_meet_founder.mp3",
    "wrong answer": "agents_wrong_answer_first_solution1.1.mp3",
    "गलत जवाब": "agents_wrong_answer_first_solution1.1.mp3",
    "recording": "agents_call_recording.mp3",
    "AI agent": "mic_drop_Iam_an_AI_agent1.1.mp3",
    "thank you": "goodbye1.mp3",
    "goodbye": "goodbye1.mp3",
    "bye": "goodbye1.mp3"
}

def get_school_response(user_input, session):
    # Check cache first (instant response!)
    user_lower = user_input.lower()
    for phrase, cached_response in response_cache.items():
        if phrase in user_lower:
            update_session_memory(cached_response, session)
            return "AUDIO", cached_response
    
    # Use Groq for intelligent snippet selection
    try:
        memory_context = "\n# SESSION MEMORY:\n"
        if session.session_memory["intro_played"]:
            memory_context += "- Intro already done - DON'T use intro files again\n"
        if session.session_memory["klariqo_explained"]:
            memory_context += "- Klariqo already explained\n"
        if session.session_memory["features_discussed"]:
            memory_context += "- Features already discussed\n"
        if session.session_memory["pricing_mentioned"]:
            memory_context += "- Pricing already mentioned\n"
        if session.session_memory["demo_offered"]:
            memory_context += "- Demo already offered\n"
        if session.session_memory["meeting_scheduled"]:
            memory_context += "- Meeting already scheduled\n"
        
        # Add call direction context
        if session.call_direction == "outbound":
            memory_context += f"- OUTBOUND CALL to {session.lead_data.get('school_name', 'school principal')}\n"
        
        base_prompt = """You are Nisha, sales agent for Klariqo. Your goal is to reply to any user input ONLY with the filenames mentioned below.
        Also besides every filename is the transcription within that particular mp3 file. So based on the user input you will analyse what they are asking,
        and then try to match their doubt or response with the best mp3 file response based on the transcript.
        Your goal is to be as detailed in every response as possible, so feel free to chain multiple filenames if relevant, for eg. "file1.mp3 + file2.mp3" etc.
        There's no limitation as to how many files you can chain, but keep in mind, you are emulating a telephonic conversation here, so it has to be detailed, but not too long.

        At any point if the user asks something that you can't answer with just a file name you will then and ONLY then, reply with a custom answer in the format as mentioned below.

        The filenames are mentioned in order of an actual conversation we had previously, so in most cases you would want to linearly play out the files. Each audio snippet or chain
        of audio snippets must make the user question for the next step. So at any point if you think the user might be left hanging, you can chain 2 mp3s together to warrant a reply
        from the user.

        As for the files that have multiple options, you can choose any randomly.

FORMAT:
- Audio files: filename(s) separated by " + "
- New response: "GENERATE: [text]"Available audio files:

# INTRODUCTIONS (first time only)
intro_klariqo1.1.mp3 | नमस्ते! मैं निशा बोल रही हूं Klariqo से, और मुझे बस 2 मिनट चाहिए आपसे to talk to you about an amazing breakthrough in tech
intro_klariqo1.2.mp3 | नमस्ते! मैं निशा बोल रही हूं Klariqo से, और मुझे बस 2 मिनट चाहिए आपसे (alternate version)

# KLARIQO EXPLANATION
klariqo_provides_voice_agent1.mp3 | बिलकुल ! तो Klariqo आपकी help करता है, आपको एक realistic and human sounding, automated voice agent provide करके।
voice_agents_trained_details.mp3 | ये Voice Agents जो होते हैं, ये पूरी तरह से आपके school के data पर train किए जाते हैं
basically_agent_answers_parents.mp3 | Basically उसके बाद जब भी कोई parents या interested candidates आपके स्कूल को कॉल करता है
agent_guides_onboarding_process.mp3 | सारे questionsको clearly clarify करने के बाद या तो यह एजेंट उनके लिए एक visit बुक करेगा

# KEY FEATURES
agents_need_no_breaks.mp3 | इस एजेंट की सबसे खास बात यह है कि ये twenty four seven काम करते हैं
klariqo_concurrent_calls.mp3 | एक और अद्भुत feature यह है कि यह एक ही time में 5 concurrent calls को handle कर सकता है
klariqo_agents_sound_so_realistic.mp3 | बहुत अच्छा question है! और सबसे अच्छी बात यह है कि हमारे agents को आप पता ही नहीं लगा पाएंगे
best_feature_concurrent_call.mp3 | हमारा सबसे अच्छा feature जो कि कुछ और स्कूलों को काफी interesting लगा

# TECHNICAL CONCERNS
agents_wrong_answer_first_solution1.1.mp3 | ofcourse I understand. अगर आप एजेंट के गलत जवाब देने से worried हैं
agents_wrong_answer_first_solution1.2.mp3 | (alternate version)
agents_wrong_answer_second_solution.mp3 | Second option होता है, कि हम agent को train करें उस information पर
agents_call_recording.mp3 | Ofcourse और यह हमारी top features में से एक है
klariqo_low_maintan_start.mp3 | जी that's a valid doubt. Ofourse आप busy होंगे with school operations

# PRICING
klariqo_pricing1.1.mp3 | हमने हमारी pricing का aim रखा है, to be as manageable for you as possible
klariqo_pricing1.2.mp3 | (alternate version) 
3000_mins_breakdown1.1.mp3 | तो हमारे पिछले experiences से, हमने notice किया कि आमतौर पर हर कॉल में average 2-3 मिनट
40_calls_everymonth1.1.mp3 | हां तो 25 days का consider करें तो 1000 कॉल से मतलब है हमारा agent daily 40 calls handle कर सकता है

# DEMO & MEETING
glad_for_demo_and_patent_mention1.1.mp3 | Fantastic! मैं आपको बताऊ, I am actually glad कि आप इस demo को देखने का decide किया
meeting_with_founder.mp3 | क्या मैं WhatsApp पे डेमो के साथ, एक मीटिंग भी शेड्यूल कर सकती हूं हमारे फाउंडर के साथ?
why_meet_founder.mp3 | I mean मैं आपको केवल basic information बता सक्ती हूं, लेकिन वह after all founder हैं
when_can_founder_call.mp3 | वैसे हमारे founder आपको कब call कर सकते हैं? To discuss the meeting and all?

# AI REVEAL & CLOSING
mic_drop_Iam_an_AI_agent1.1.mp3 | बहुत अच्छा लगा आपसे बात करके। वैसे मैं wait कर रही थी इसके बारे में बताने के लिए
goodbye1.mp3 | Ok thank you very much for your time. Was a pleasure talking to you. Have a great day!

"""
        
        full_prompt = base_prompt + memory_context
        
        # GROQ ULTRA-FAST CALL
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.2,
            max_tokens=50
        )
        
        groq_response = response.choices[0].message.content.strip()
        groq_response = groq_response.replace('"', '').replace("'", "")
        
        update_session_memory(groq_response, session)
        
        if groq_response.startswith("GENERATE:"):
            text_to_generate = groq_response.replace("GENERATE:", "").strip()
            return "TTS", text_to_generate
        else:
            return "AUDIO", groq_response
            
    except:
        return "AUDIO", "klariqo_provides_voice_agent1.mp3"

def update_session_memory(audio_files, session):
    files_str = audio_files.lower()
    if any(intro in files_str for intro in ["intro_klariqo1.1", "intro_klariqo1.2"]):
        session.session_memory["intro_played"] = True
    if any(explain in files_str for explain in ["klariqo_provides_voice_agent1", "voice_agents_trained_details"]):
        session.session_memory["klariqo_explained"] = True
    if any(feature in files_str for feature in ["agents_need_no_breaks", "klariqo_concurrent_calls", "best_feature"]):
        session.session_memory["features_discussed"] = True
    if any(price in files_str for price in ["klariqo_pricing1", "3000_mins_breakdown1", "40_calls_everymonth1"]):
        session.session_memory["pricing_mentioned"] = True
    if any(demo in files_str for demo in ["glad_for_demo_and_patent_mention1"]):
        session.session_memory["demo_offered"] = True
    if any(meeting in files_str for meeting in ["meeting_with_founder", "why_meet_founder", "when_can_founder_call"]):
        session.session_memory["meeting_scheduled"] = True

def generate_tts_audio(text):
    try:
        audio_stream = elevenlabs_client.text_to_speech.stream(
            text=text,
            voice_id=VOICE_ID,
            model_id="eleven_flash_v2_5",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.8,
                style=0.0,
                use_speaker_boost=False
            )
        )
        
        audio_data = b""
        for chunk in audio_stream:
            if chunk:
                audio_data += chunk
        
        if audio_data:
            temp_filename = f"temp_tts_{int(time.time())}.mp3"
            with open(temp_filename, 'wb') as f:
                f.write(audio_data)
            return temp_filename
        return None
    except:
        return None

# =============== OUTBOUND CALLING FUNCTIONS ===============

def make_outbound_call(target_number, lead_data):
    """Make an outbound call to a school"""
    try:
        print(f"📞 Calling {lead_data.get('school_name')} at {target_number}")
        
        call = twilio_client.calls.create(
            to=target_number,
            from_=TWILIO_PHONE,
            url=f"{current_ngrok_url}/twilio/outbound/{lead_data['id']}",
            method='POST'
        )
        
        # Store call info
        active_outbound_calls[call.sid] = {
            'lead_data': lead_data,
            'start_time': time.time(),
            'status': 'calling'
        }
        
        print(f"✅ Outbound call initiated: {call.sid}")
        return call.sid
        
    except Exception as e:
        print(f"❌ Failed to make outbound call: {e}")
        return None

def start_school_calling_campaign(target_list, max_calls=50):
    """Start mass outbound calling campaign to schools"""
    
    call_count = 0
    for school in target_list:
        if call_count >= max_calls:
            break
            
        # Check if already called today  
        if not school.get('called_today', False):
            call_sid = make_outbound_call(school['phone'], school)
            
            if call_sid:
                call_count += 1
                # Wait between calls (be respectful!)
                time.sleep(10)  # 10 seconds between calls
                
        if call_count >= max_calls:
            break
    
    print(f"🚀 School campaign complete: {call_count} calls made")

# Global tracking
active_outbound_calls = {}

# =============== TWILIO HANDLERS ===============

@app.route("/", methods=['GET'])
def health_check():
    return "🚀 Klariqo School System - Ultra-Fast Streaming!"

@app.route("/twilio/voice", methods=['POST'])
def handle_incoming_call():
    """Handle INBOUND calls"""
    caller = request.form.get('From', 'Unknown')
    call_sid = request.form.get('CallSid', 'unknown')
    
    print(f"📞 INBOUND call from {caller}")
    
    # Create INBOUND session
    session = StreamingSession(call_sid, call_direction="inbound")
    active_sessions[call_sid] = session
    
    response = VoiceResponse()
    
    # Inbound intro (demo mode)
    import random
    intro_options = ["intro_klariqo1.1.mp3", "intro_klariqo1.2.mp3"]
    selected_intro = random.choice(intro_options)
    
    session.session_memory["intro_played"] = True
    
    intro_url = f"{request.url_root}audio/{selected_intro}"
    response.play(intro_url)
    
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media/{call_sid}')
    connect.append(stream)
    response.append(connect)
    
    return str(response)

@app.route("/twilio/outbound/<lead_id>", methods=['POST'])
def handle_outbound_call(lead_id):
    """Handle OUTBOUND calls"""
    call_sid = request.form.get('CallSid', 'unknown')
    
    # Get lead data
    lead_data = {'id': lead_id, 'school_name': 'School Principal', 'type': 'school'}
    
    print(f"📞 OUTBOUND call connected to {lead_data['school_name']}")
    
    # Create OUTBOUND session
    session = StreamingSession(call_sid, call_direction="outbound", lead_data=lead_data)
    active_sessions[call_sid] = session
    
    response = VoiceResponse()
    
    # Outbound intro (sales mode)
    selected_intro = "intro_klariqo1.1.mp3"
    session.session_memory["intro_played"] = True
    
    intro_url = f"{request.url_root}audio/{selected_intro}"
    response.play(intro_url)
    
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media/{call_sid}')
    connect.append(stream)
    response.append(connect)
    
    return str(response)

@sock.route('/media/<call_sid>')
def media_stream(ws, call_sid):
    """Handle streaming audio - works for BOTH inbound and outbound!"""
    session = active_sessions.get(call_sid)
    if not session:
        return
    
    session.twilio_ws = ws
    
    # Same streaming logic for both directions
    def start_deepgram():
        try:
            options = LiveOptions(
                model="nova-2",
                language="hi",
                punctuate=True,
                smart_format=True,
                sample_rate=8000,
                encoding="linear16",
                channels=1,
                interim_results=True,
            )
            
            session.dg_connection = deepgram.listen.websocket.v("1")
            session.dg_connection.on(LiveTranscriptionEvents.Transcript, session.on_deepgram_message)
            session.dg_connection.on(LiveTranscriptionEvents.Error, session.on_deepgram_error)
            session.dg_connection.on(LiveTranscriptionEvents.Open, session.on_deepgram_open)
            session.dg_connection.start(options)
        except:
            pass
    
    deepgram_thread = threading.Thread(target=start_deepgram)
    deepgram_thread.daemon = True
    deepgram_thread.start()
    time.sleep(0.5)
    
    def transcript_checker():
        while True:
            time.sleep(0.05)
            if session.check_for_completion():
                redirect_to_processing(session.completed_transcript, call_sid)
                break
    
    checker_thread = threading.Thread(target=transcript_checker)
    checker_thread.daemon = True
    checker_thread.start()
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
            data = json.loads(message)
            if data.get('event') == 'media':
                if session.dg_connection:
                    media_payload = data.get('media', {}).get('payload', '')
                    if media_payload:
                        try:
                            mulaw_data = base64.b64decode(media_payload)
                            linear_data = audioop.ulaw2lin(mulaw_data, 2)
                            session.dg_connection.send(linear_data)
                        except:
                            pass
            elif data.get('event') == 'stop':
                break
    except:
        pass
    finally:
        if session.dg_connection:
            session.dg_connection.finish()
            session.dg_connection = None

def redirect_to_processing(transcript, call_sid):
    try:
        session = active_sessions.get(call_sid)
        if not session:
            return
        
        response_type, content = get_school_response(transcript, session)
        
        session.next_response_type = response_type
        session.next_response_content = content
        session.next_transcript = transcript
        session.ready_for_twiml = True
        
        # Chat output with call direction
        direction_emoji = "📞" if session.call_direction == "inbound" else "🏫"
        if response_type == "AUDIO":
            print(f"{direction_emoji} Principal: {transcript}")
            print(f"{direction_emoji} Nisha: <audio: {content}>")
        else:
            print(f"{direction_emoji} Principal: {transcript}")
            print(f"{direction_emoji} Nisha: <TTS: {content}>")
        
        global current_ngrok_url
        if 'current_ngrok_url' in globals():
            twiml_url = f"{current_ngrok_url}/twilio/continue/{call_sid}"
            twilio_client.calls(call_sid).update(url=twiml_url, method='POST')
    except:
        pass

@app.route("/twilio/continue/<call_sid>", methods=['POST'])
def continue_conversation(call_sid):
    """Continue conversation - works for both inbound and outbound"""
    try:
        session = active_sessions.get(call_sid)
        if not session or not hasattr(session, 'ready_for_twiml'):
            response = VoiceResponse()
            response.say("Processing error")
            response.hangup()
            return str(response)
        
        response_type = session.next_response_type
        content = session.next_response_content
        transcript = session.next_transcript
        
        session.conversation_history.append(f"Principal: {transcript}")
        session.conversation_history.append(f"Nisha: {content}")
        
        twiml_response = VoiceResponse()
        
        if response_type == "AUDIO":
            audio_files = [f.strip() for f in content.split('+')]
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    audio_url = f"{request.url_root}audio/{audio_file}"
                    twiml_response.play(audio_url)
        
        elif response_type == "TTS":
            tts_file = generate_tts_audio(content)
            if tts_file:
                tts_url = f"{request.url_root}audio/{tts_file}"
                twiml_response.play(tts_url)
            else:
                twiml_response.say("Sorry, I'm having trouble generating audio.")
        
        if any(word in content.lower() for word in ["goodbye", "goodbye1.mp3"]):
            twiml_response.hangup()
            if call_sid in active_sessions:
                del active_sessions[call_sid]
        else:
            session.accumulated_text = ""
            session.last_activity_time = None
            session.is_processing = False
            session.completed_transcript = None
            session.transcript_ready = False
            session.ready_for_twiml = False
            
            connect = Connect()
            stream = Stream(url=f'wss://{request.host}/media/{call_sid}')
            connect.append(stream)
            twiml_response.append(connect)
        
        session.ready_for_twiml = False
        return str(twiml_response)
    except:
        response = VoiceResponse()
        response.say("I'm having technical difficulties.")
        response.hangup()
        return str(response)

@app.route("/audio/<filename>")
def serve_audio(filename):
    try:
        if os.path.exists(filename):
            return send_file(filename, mimetype='audio/mpeg')
        else:
            return "Audio file not found", 404
    except:
        return "Error serving audio", 500

# =============== TESTING ENDPOINTS ===============

@app.route("/call_test/<phone_number>", methods=['GET'])
def call_test(phone_number):
    """Browser-friendly test endpoint - call any number"""
    try:
        # Add + if not present
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
            
        lead_data = {
            'id': 'test_123',
            'school_name': 'Test School Demo',
            'type': 'test'
        }
        
        call_sid = make_outbound_call(phone_number, lead_data)
        
        if call_sid:
            return f"""
            <h2>✅ Klariqo School Demo Call Initiated!</h2>
            <p><strong>Calling:</strong> {phone_number}</p>
            <p><strong>Call ID:</strong> {call_sid}</p>
            <p><strong>Agent:</strong> Nisha from Klariqo</p>
            <p><strong>Status:</strong> Your phone should ring in 5-10 seconds!</p>
            <br>
            <p>🎭 <strong>Pretend to be a school principal!</strong></p>
            <p>💡 Try asking: "What is Klariqo?", "How much?", "Demo?"</p>
            <p>🎬 The AI will reveal itself at the end!</p>
            """
        else:
            return "<h2>❌ Failed to make call</h2><p>Check logs for errors</p>"
            
    except Exception as e:
        return f"<h2>❌ Error</h2><p>{str(e)}</p>"

@app.route("/test")
def test_page():
    """Simple test page"""
    return f"""
    <h1>🚀 Klariqo School System - Ultra-Fast Streaming!</h1>
    <h3>📞 Test School Sales Call:</h3>
    <p>Nisha will call you to pitch Klariqo:</p>
    <ul>
        <li><a href="/call_test/919876543210">Call +91-9876543210 (Update with your number)</a></li>
        <li><a href="/call_test/919039832599">Call +91-9039832599</a></li>
    </ul>
    
    <h3>📊 Active Sessions:</h3>
    <p>Currently active calls: {len(active_sessions)}</p>
    
    <h3>🎯 Campaign Status:</h3>
    <p>Outbound calls made: {len(active_outbound_calls)}</p>
    
    <br>
    <p><strong>Instructions:</strong></p>
    <ol>
        <li>Click a test link above (update phone number first)</li>
        <li>Your phone should ring in 5-10 seconds</li>
        <li>Answer the call and pretend to be a school principal</li>
        <li>Nisha will pitch Klariqo to you with ultra-fast streaming!</li>
        <li>Ask questions and experience the demo!</li>
    </ol>
    
    <p><strong>🎬 Your product is selling itself - at lightning speed!</strong></p>
    """

# =============== CAMPAIGN MANAGEMENT ===============

@app.route("/start_campaign", methods=['POST'])
def start_campaign():
    """API endpoint to start school calling campaign"""
    try:
        # Sample school data (you'll load from CSV/database)
        sample_schools = [
            {'id': '1', 'school_name': 'DPS School Delhi', 'phone': '+91XXXXXXXXXX', 'type': 'school'},
            {'id': '2', 'school_name': 'Ryan International', 'phone': '+91XXXXXXXXXX', 'type': 'school'},
            # Add more schools...
        ]
        
        # Start campaign in background
        campaign_thread = threading.Thread(
            target=start_school_calling_campaign, 
            args=(sample_schools, 10)  # Start with 10 calls
        )
        campaign_thread.daemon = True
        campaign_thread.start()
        
        return {"status": "success", "message": "School campaign started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def start_ngrok():
    import subprocess
    import time
    try:
        process = subprocess.Popen([
            'ngrok', 'http', '5000', '--log=stdout'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        import json
        import urllib.request
        try:
            with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
                data = json.loads(response.read())
                public_url = data['tunnels'][0]['public_url']
                return public_url
        except:
            return None
    except FileNotFoundError:
        return None

if __name__ == "__main__":
    print("🚀 KLARIQO SCHOOL SYSTEM")
    print("🏫 AI Sales Agent: Nisha")
    print("⚡ ULTRA-FAST STREAMING (Original Architecture)")
    print("🦙 Powered by Groq Llama-3.1-8b-instant")
    print("🎯 Target: School Principals")
    print("=" * 50)
    
    public_url = start_ngrok()
    global current_ngrok_url
    current_ngrok_url = public_url
    
    if public_url:
        print(f"Inbound Webhook: {public_url}/twilio/voice")
        print(f"Campaign API: {public_url}/start_campaign")
        print(f"🧪 TEST PAGE: {public_url}/test")
        print(f"🎯 QUICK TEST: {public_url}/call_test/YOUR_PHONE_NUMBER")
        print("🔥 Ready for ultra-fast school demos!")
        print()
        print("🧪 TO TEST SCHOOL DEMO:")
        print(f"1. Visit: {public_url}/test")
        print(f"2. Or directly: {public_url}/call_test/919876543210")
        print("3. Replace with your actual phone number!")
        print("4. Answer as a school principal")
        print("5. Experience Nisha selling Klariqo at lightning speed!")
        print()
        print("🎯 TO START MASS CAMPAIGN:")
        print(f"POST {public_url}/start_campaign")
        print()
        print("✅ ORIGINAL HOTEL STREAMING ARCHITECTURE PRESERVED!")
        print("⚡ ONLY BUSINESS LOGIC CHANGED TO SCHOOL SALES!")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)