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
    
    def _build_base_prompt(self):
        """Build the base prompt for GPT response selection"""
        
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
        """Build lightweight context prompt with memory (saves tokens!)"""
        
        # Get recent conversation history
        recent_files = self._get_recent_files(session, limit=3)
        recent_conversation = self._get_recent_conversation(session, limit=2)
        
        context_prompt = f"""
🧠 CONVERSATION MEMORY:
Recently played files (DON'T repeat): {', '.join(recent_files)}
Recent conversation: {recent_conversation}

📝 CURRENT USER INPUT: "{user_input}"

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