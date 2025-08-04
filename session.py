#!/usr/bin/env python3
"""
KLARIQO SESSION MANAGEMENT MODULE
Handles call session states for both inbound and outbound calls
"""

import time
from config import Config

class StreamingSession:
    """Manages individual call session state and memory"""
    
    def __init__(self, call_sid, call_direction="inbound", lead_data=None):
        self.call_sid = call_sid
        self.call_direction = call_direction  # "inbound" or "outbound"
        self.lead_data = lead_data or {}  # School info for outbound calls
        
        # Session memory - tracks what has been discussed
        self.session_memory = Config.SESSION_FLAGS_TEMPLATE.copy()
        
        # Dynamic session variables - tracks specific information gathered during conversation
        self.session_variables = Config.SESSION_VARIABLES_TEMPLATE.copy()
        
        # Conversation tracking
        self.conversation_history = []
        self.accumulated_text = ""
        self.last_activity_time = None
        self.silence_threshold = Config.SILENCE_THRESHOLD
        
        # Processing state
        self.is_processing = False
        self.completed_transcript = None
        self.transcript_ready = False
        
        # Connection objects
        self.dg_connection = None  # Deepgram WebSocket
        self.twilio_ws = None      # Twilio WebSocket
        
        # Response preparation
        self.next_response_type = None
        self.next_response_content = None  
        self.next_transcript = None
        self.ready_for_twiml = False
    
    def on_deepgram_open(self, *args, **kwargs):
        """Handle Deepgram connection opening"""
        # Removed debug print for cleaner logs
        pass
    
    def on_deepgram_message(self, *args, **kwargs):
        """Process incoming speech transcription from Deepgram"""
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
        """Handle Deepgram connection errors"""
        error = kwargs.get('error', 'Unknown error')
        print(f"❌ Deepgram error for call {self.call_sid}: {error}")
    
    def check_for_completion(self):
        """Check if user has finished speaking based on silence threshold"""
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
    
    def add_to_history(self, speaker, message):
        """Add message to conversation history"""
        timestamp = time.strftime("%H:%M:%S")
        self.conversation_history.append(f"[{timestamp}] {speaker}: {message}")
    
    def update_session_variable(self, variable_name, value):
        """Update a specific session variable"""
        if variable_name in self.session_variables:
            old_value = self.session_variables[variable_name]
            self.session_variables[variable_name] = value
            print(f"📝 Updated {variable_name}: {old_value} → {value}")
            return True
        return False
    
    def get_session_context(self):
        """Get current session context for AI prompt"""
        context = []
        
        # Add dynamic variables with values
        for var, value in self.session_variables.items():
            if value is not None:
                context.append(f"{var}: {value}")
        
        # Add conversation flags
        active_flags = [flag for flag, status in self.session_memory.items() if status]
        if active_flags:
            context.append(f"Discussed topics: {', '.join(active_flags)}")
        
        return " | ".join(context) if context else "No context yet"
    
    def get_formatted_session_context(self):
        """Get formatted session context for AI prompts (legacy method)"""
        context = "\n# SESSION MEMORY:\n"
        if self.session_memory["intro_played"]:
            context += "- Intro already done - DON'T use intro files again\n"
        if self.session_memory["admission_process_explained"]:
            context += "- Admission process already explained\n"
        if self.session_memory["features_discussed"]:
            context += "- Features already discussed\n"
        if self.session_memory["pricing_mentioned"]:
            context += "- Pricing already mentioned\n"
        if self.session_memory["demo_offered"]:
            context += "- Demo already offered\n"
        if self.session_memory["meeting_scheduled"]:
            context += "- Meeting already scheduled\n"
        
        # Add call direction context
        if self.call_direction == "outbound":
            school_name = self.lead_data.get('school_name', 'parent/guardian')
            context += f"- OUTBOUND CALL to {school_name}\n"
        
        return context
    
    def reset_for_next_input(self):
        """Reset session state for next user input"""
        self.accumulated_text = ""
        self.last_activity_time = None
        self.is_processing = False
        self.completed_transcript = None
        self.transcript_ready = False
        self.ready_for_twiml = False
    
    def cleanup(self):
        """Clean up session resources"""
        try:
            if self.dg_connection:
                self.dg_connection.finish()
                self.dg_connection = None
        except Exception as e:
            print(f"⚠️ Error cleaning up session {self.call_sid}: {e}")


class SessionManager:
    """Manages multiple concurrent call sessions"""
    
    def __init__(self):
        self.active_sessions = {}
        self.active_outbound_calls = {}
    
    def create_session(self, call_sid, call_direction="inbound", lead_data=None):
        """Create new session for incoming call"""
        session = StreamingSession(call_sid, call_direction, lead_data)
        self.active_sessions[call_sid] = session
        
        # Only show session creation for debugging if needed
        # direction_emoji = "📞" if call_direction == "inbound" else "🏫"
        # print(f"{direction_emoji} New session created: {call_sid}")
        
        return session
    
    def get_session(self, call_sid):
        """Get existing session by call SID"""
        return self.active_sessions.get(call_sid)
    
    def remove_session(self, call_sid):
        """Remove and cleanup session"""
        session = self.active_sessions.pop(call_sid, None)
        if session:
            session.cleanup()
            # Removed cleanup log for cleaner output
        
        # Also remove from outbound tracking if exists
        self.active_outbound_calls.pop(call_sid, None)
    
    def get_active_count(self):
        """Get count of active sessions"""
        return len(self.active_sessions)
    
    def track_outbound_call(self, call_sid, lead_data):
        """Track outbound call metadata"""
        self.active_outbound_calls[call_sid] = {
            'lead_data': lead_data,
            'start_time': time.time(),
            'status': 'calling'
        }

# Global session manager instance
session_manager = SessionManager()