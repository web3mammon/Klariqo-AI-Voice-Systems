#!/usr/bin/env python3
"""
KLARIQO GEMINI ROUTER MODULE  
Fast response selection using Google Gemini Flash
"""

import google.generativeai as genai
from config import Config
from audio_manager import audio_manager

# Initialize Gemini client
genai.configure(api_key=Config.GEMINI_API_KEY)

class ResponseRouterGemini:
    """Handles AI-powered response selection with Google Gemini Flash"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.base_prompt = self._build_base_prompt()
        print("💎 Gemini Flash Router initialized: FAST mode (150-250ms responses)")
    
    def _build_base_prompt(self):
        """Build the base prompt for Gemini response selection"""
        
        # Get available files for dynamic selection
        available_files = self._get_available_files_by_category()
        
        prompt = f"""You are Nisha's audio file selector for Klariqo sales calls. Your ONLY job is to match user input to the correct audio files below.

🚨 CRITICAL RULES:
- Reply with ONLY filenames (e.g., "file1.mp3 + file2.mp3")  
- If NO rule matches, reply "GENERATE: I want to help you in the best way possible. Could you tell me what specific aspect you'd like to know more about?"
- DO NOT repeat files that were recently played (check conversation memory)
- 🚫 NEVER EVER include intro files (intro_klariqo*.mp3) - The intro has ALREADY been played during call setup
- This is a cold call where intro is DONE - focus on the conversation flow only

📋 AVAILABLE FILES BY CATEGORY:
{available_files}

📋 EXACT MATCHING RULES:

User shows interest/asks to tell more (बताइए, tell me, interesting, go ahead, yes, sure) → klariqo_provides_voice_agent1.mp3 + voice_agents_trained_details.mp3 + basically_agent_answers_parents.mp3 + agent_guides_onboarding_process.mp3

User asks how this helps if they already have receptionist/team → agents_need_no_breaks.mp3 + klariqo_concurrent_calls.mp3

User asks if people can tell it's AI/computer voice → klariqo_agents_sound_so_realistic.mp3 + klariqo_agents_sound_so_realistic2.mp3

User asks what if AI gives wrong response/gets broken → agents_wrong_answer_first_solution.mp3 + agents_wrong_answer_second_solution.mp3

User asks how it works/setup/time consuming → klariqo_low_maintan_start.mp3 + klariqo_adding_extra_features.mp3

User asks if this is app/software/technical working → how_does_it_work_tech.mp3 + klariqo_adding_extra_features.mp3

User asks about technical failure → tech_stability_and_safety_net.mp3

User asks examples of other clients → client_examples_bhopal1.mp3

User asks about guaranteed results → proof_of_improvement1.mp3

User asks pricing/cost/fees → klariqo_pricing.mp3 + 3000_mins_breakdown.mp3 + 40_calls_everymonth.mp3

User says don't need now/will consider later → beyond_admissions_outreach.mp3

User asks about call recording/transcripts → agents_call_recording.mp3

User asks about minutes expiring/need extra → minutes_about_to_expire_fallback.mp3 + additional_minute_option_second_agent.mp3 + additional_minute_option_topup.mp3

User wants demo/mentions WhatsApp demo → glad_for_demo_and_patent_mention.mp3 + meeting_with_founder.mp3

User asks about patent details → founder_filed_patent.mp3

User asks why meet founder → why_meet_founder.mp3 + when_can_founder_call.mp3

User agrees to demo/founder meeting → mic_drop_Iam_an_AI_agent.mp3

User acts surprised about AI reveal → shocked_after_agent_reveal_response.mp3

User wants to end conversation → goodbye1.mp3

🚫 FORBIDDEN: Never suggest intro_klariqo files - intro is already done!"""
        
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
        
        for class_key, class_value in class_mappings.items():
            if class_key in user_lower:
                session.update_session_variable("admission_class", class_value)
                break
        
        # Extract location information
        location_keywords = ["location", "area", "locality", "address", "where", "कहाँ", "जगह"]
        if any(keyword in user_lower for keyword in location_keywords):
            # Simple extraction - could be enhanced with NLP
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in location_keywords and i + 1 < len(words):
                    location = words[i + 1]
                    session.update_session_variable("student_location", location)
                    break
        
        # Extract age information
        import re
        age_pattern = r'(\d+)\s*(?:years?|saal|उम्र)'
        age_match = re.search(age_pattern, user_lower)
        if age_match:
            age = age_match.group(1)
            session.update_session_variable("student_age", age)
        
        # Extract inquiry focus
        focus_keywords = {
            "fees": ["fees", "fee", "charges", "cost", "price", "फीस"],
            "admission": ["admission", "admit", "enroll", "admission", "प्रवेश"],
            "transport": ["transport", "bus", "vehicle", "pickup", "drop", "परिवहन"],
            "activities": ["activities", "sports", "games", "extra", "activities", "गतिविधियां"],
            "timings": ["timing", "time", "schedule", "hours", "समय"],
            "security": ["security", "safety", "protection", "सुरक्षा"]
        }
        
        for focus, keywords in focus_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                session.update_session_variable("inquiry_focus", focus)
                break

    def get_school_response(self, user_input, session):
        """Get appropriate response for school conversation - GEMINI FLASH MODE"""
        
        try:
            import time
            start = time.time()
            
            # Build the full prompt for Gemini
            full_prompt = f"{self.base_prompt}\n\n{self._build_context_prompt(session, user_input)}"
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Very low for consistency
                max_output_tokens=100,  # Limit response length
                top_p=0.8,
                top_k=20
            )
            
            # Call Google Gemini Flash
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            gemini_response = response.text.strip()
            gemini_response = gemini_response.replace('"', '').replace("'", "")
            
            response_time = int((time.time() - start) * 1000)
            
            # Check if it's a custom generation request
            if gemini_response.startswith("GENERATE:"):
                text_to_generate = gemini_response.replace("GENERATE:", "").strip()
                print(f"💎 Gemini → TTS: {text_to_generate} ({response_time}ms)")
                return "TTS", text_to_generate
            else:
                print(f"💎 Gemini → Audio: {gemini_response} ({response_time}ms)")
                return "AUDIO", gemini_response
                
        except Exception as e:
            # Fallback to safe response
            print(f"❌ Gemini error: {e}")
            return "TTS", "I want to make sure I give you the right information. Could you tell me what specific aspect you'd like to know more about?"
    
    def validate_response(self, response_content):
        """Validate that the response contains valid audio files"""
        if not response_content or response_content.startswith("GENERATE:"):
            return True
        
        # Validate audio chain
        return audio_manager.validate_audio_chain(response_content)

# Global Gemini response router instance
response_router_gemini = ResponseRouterGemini()