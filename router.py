#!/usr/bin/env python3
"""
KLARIQO RESPONSE ROUTER MODULE  
Clean GPT-based response selection with reliable TTS handling
"""

from openai import OpenAI
from config import Config
from audio_manager import audio_manager

# Initialize OpenAI client
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

class ResponseRouter:
    """Handles AI-powered response selection with reliable GPT processing"""
    
    def __init__(self):
        self.base_prompt = self._build_base_prompt()
        print("🤖 Response Router initialized: GPT-only mode (reliable & fast)")
    
    def _extract_session_variables(self, user_input, session):
        """Extract and update session variables from user input"""
        user_lower = user_input.lower()
        
        # Extract admission type
        if any(word in user_lower for word in ["first time", "firsttime", "pehli bar", "naya admission"]):
            session.update_session_variable("admission_type", "firsttime")
        elif any(word in user_lower for word in ["transfer", "dusre school se", "change school"]):
            session.update_session_variable("admission_type", "transfer")
        
        # Extract class information
        class_mappings = {
            "kg1": "KG1", "kg 1": "KG1", "nursery": "KG1", "pre kg": "KG1",
            "kg2": "KG2", "kg 2": "KG2", "ukg": "KG2",
            "1st class": "Class 1", "class 1": "Class 1", "first class": "Class 1", "पहली क्लास": "Class 1",
            "2nd class": "Class 2", "class 2": "Class 2", "second class": "Class 2", "दूसरी क्लास": "Class 2",
            "3rd class": "Class 3", "class 3": "Class 3", "third class": "Class 3", "तीसरी क्लास": "Class 3",
            "4th class": "Class 4", "class 4": "Class 4", "fourth class": "Class 4", "चौथी क्लास": "Class 4",
            "5th class": "Class 5", "class 5": "Class 5", "fifth class": "Class 5", "पांचवी क्लास": "Class 5"
        }
        
        for key, value in class_mappings.items():
            if key in user_lower:
                session.update_session_variable("admission_class", value)
                break
        
        # Extract location for bus route
        location_indicators = ["area", "location", "jagah", "रहते हैं", "से आना है", "pick up"]
        if any(indicator in user_lower for indicator in location_indicators):
            # Extract the location (simplified - could be enhanced with NLP)
            words = user_input.split()
            for i, word in enumerate(words):
                if any(indicator in word.lower() for indicator in location_indicators):
                    if i > 0:
                        potential_location = words[i-1]
                        session.update_session_variable("student_location", potential_location)
                    break
        
        # Extract age information
        import re
        age_match = re.search(r'(\d+)\s*(?:years?|साल|वर्ष)', user_lower)
        if age_match:
            age = int(age_match.group(1))
            session.update_session_variable("student_age", age)
        
        # Extract inquiry focus
        if any(word in user_lower for word in ["fees", "fee", "फीस", "cost", "charges"]):
            session.update_session_variable("inquiry_focus", "fees")
        elif any(word in user_lower for word in ["transport", "bus", "बस", "pickup"]):
            session.update_session_variable("inquiry_focus", "transport")
        elif any(word in user_lower for word in ["activity", "activities", "sports", "खेल"]):
            session.update_session_variable("inquiry_focus", "activities")
        elif any(word in user_lower for word in ["admission", "एडमिशन", "दाखिला"]):
            session.update_session_variable("inquiry_focus", "admission")
    
    def _build_base_prompt(self):
        """Build the base prompt for GPT response selection"""
        
        # Get available files for dynamic selection
        available_files = self._get_available_files_by_category()
        
        prompt = f"""You are Nisha's audio file selector — a polite, helpful voice assistant at AVS International School. Your job is to respond to parent queries with the right audio file snippet(s) from the school's library.

🚨 CRITICAL RULES:
Always reply using only the correct filenames (e.g., admission_process_firsttime.mp3 + school_timings.mp3)

Never repeat a file that was recently played during this session

If you’re unsure what to play, use:
GENERATE: कृपया थोड़ा और स्पष्ट करें कि आप क्या जानना चाहते हैं?

📋 DYNAMIC SESSION VARIABLES YOU TRACK:
Variable	Purpose	Example Values
admission_type	Type of admission	"firsttime" or "transfer"
admission_class	Class for admission	"KG1", "KG2", "Class 1", "Class 2", etc.
student_location	Location for bus route	Area/locality name for transport
student_age	Age for eligibility	Numeric age in years
inquiry_focus	Main topic of interest	"fees", "transport", "admission", "activities"

📋 INTELLIGENT AUDIO SELECTION RULES:
Parent Input	Play These (based on session variables)
Asks about admission (general)	
→ If admission_type="firsttime": admission_process_firsttime.mp3
→ If admission_type="transfer": admission_process_transfer.mp3
→ If unknown: fees_ask_class.mp3 (to gather more info)

Mentions class + asks fees	
→ If admission_class known: Use specific fee audio for that class
→ If unknown: fees_ask_class.mp3 first

Asks transport/bus availability	
→ If student_location unknown: bus_ask_location.mp3
→ If student_location known: bus_fees.mp3

Says age/mentions child's age	admission_age_eligibility.mp3

Standard queries (use existing logic):
→ Asks timings: school_timings.mp3
→ Asks CBSE: cbse_based.mp3  
→ Asks activities: extra_activities.mp3
→ Asks security: security.mp3
→ Asks scholarships: scholarships_n_discounts.mp3
→ Asks smart classes: smart_classes.mp3
→ First time caller: school_intro.mp3

📤 EXAMPLES OF OUTBOUND USAGE (When School Calls Parent)
Situation	Use These Files
Calling for event invite	nisha_introduction_outbound.mp3 + annual_function_invite.mp3
Following up on admission	nisha_introduction_outbound.mp3 + admission_last_date.mp3
Announcing scholarship availability	nisha_introduction_outbound.mp3 + scholarships_n_discounts.mp3

📋 AVAILABLE AUDIO FILES:
{available_files}"""
        
        return prompt
    
    def _get_available_files_by_category(self):
        """Get formatted list of available files by category (excluding intro files)"""
        categories = []
        for category, files in audio_manager.audio_snippets.items():
            if category != "quick_responses" and files:
                # Filter out intro files from the available files list
                filtered_files = {k: v for k, v in files.items() if not k.startswith('intro_klariqo')}
                if filtered_files:
                    file_list = ", ".join(filtered_files.keys())
                    categories.append(f"{category}: {file_list}")
        return "\n".join(categories)
    
    # Remove the _get_alternatives method completely since no more alternate files
    
    def _get_recent_files(self, session, limit=3):
        """Get recently played audio files to avoid repetition"""
        recent_files = []
        
        # Look through recent conversation history for audio responses
        if hasattr(session, 'conversation_history'):
            for entry in session.conversation_history[-6:]:  # Last 6 entries
                if "Nisha:" in entry and "<audio:" in entry:
                    # Extract filenames from "<audio: file1.mp3 + file2.mp3>"
                    import re
                    files = re.findall(r'<audio: ([^>]+)>', entry)
                    if files:
                        audio_chain = files[0]
                        file_list = [f.strip() for f in audio_chain.split('+')]
                        recent_files.extend(file_list)
        
        # Return last N unique files
        seen = set()
        unique_recent = []
        for f in reversed(recent_files):
            if f not in seen and len(unique_recent) < limit:
                unique_recent.append(f)
                seen.add(f)
        
        return unique_recent[:limit]
    
    def _get_recent_conversation(self, session, limit=2):
        """Get recent conversation context"""
        if not hasattr(session, 'conversation_history'):
            return "None"
        
        recent = session.conversation_history[-(limit*2):]  # Last N exchanges
        return " | ".join(recent) if recent else "None"
    
    def _build_context_prompt(self, session, user_input):
        """Build context prompt with dynamic session variables"""
        
        # Extract and update session variables from user input
        self._extract_session_variables(user_input, session)
        
        # Get recent conversation history
        recent_files = self._get_recent_files(session, limit=3)
        recent_conversation = self._get_recent_conversation(session, limit=2)
        
        # Get current session context
        session_context = session.get_session_context()
        
        context_prompt = f"""
🧠 CONVERSATION MEMORY:
Recently played files (DON'T repeat): {', '.join(recent_files)}
Recent conversation: {recent_conversation}

📋 CURRENT SESSION VARIABLES:
{session_context}

📝 CURRENT USER INPUT: "{user_input}"

🎯 INTELLIGENT SELECTION RULES:
- If admission_type is known, use specific admission_process_firsttime.mp3 or admission_process_transfer.mp3
- If admission_class is known and user asks about fees, use fees_ask_class.mp3 then mention specific fees for that class
- If student_location is provided and user asks about transport, use bus_fees.mp3 with location context
- If student_age is known, use admission_age_eligibility.mp3 for age-related queries

Apply the rules from your system prompt. Choose appropriate files or GENERATE response."""
        
        return context_prompt
    
    def get_school_response(self, user_input, session):
        """Get appropriate response for school conversation - RELIABLE GPT-ONLY MODE"""
        
        try:
            import time
            start = time.time()
            
            # Build messages with cached system prompt + lightweight context
            messages = [
                {"role": "system", "content": self.base_prompt},
                {"role": "user", "content": self._build_context_prompt(session, user_input)}
            ]
            
            # Call OpenAI GPT-3.5-turbo for response
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.1,  # Very low for consistency
                max_tokens=100,   # Allow longer responses for chaining
                timeout=10        # 10 second timeout
            )
            
            openai_response = response.choices[0].message.content.strip()
            openai_response = openai_response.replace('"', '').replace("'", "")
            
            response_time = int((time.time() - start) * 1000)
            
            # Check if it's a custom generation request
            if openai_response.startswith("GENERATE:"):
                text_to_generate = openai_response.replace("GENERATE:", "").strip()
                print(f"🎯 GPT → TTS: {text_to_generate} ({response_time}ms)")
                return "TTS", text_to_generate
            else:
                print(f"🎯 GPT → Audio: {openai_response} ({response_time}ms)")
                return "AUDIO", openai_response
                
        except Exception as e:
            # Fallback to safe response
            print(f"❌ GPT error: {e}")
            return "TTS", "I want to make sure I give you the right information. Could you tell me what specific aspect you'd like to know more about?"
    
    def validate_response(self, response_content):
        """Validate that the response contains valid audio files"""
        if not response_content or response_content.startswith("GENERATE:"):
            return True
        
        # Validate audio chain
        return audio_manager.validate_audio_chain(response_content)

# Global response router instance
response_router = ResponseRouter()