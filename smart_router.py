#!/usr/bin/env python3
"""
KLARIQO SMART ROUTER MODULE  
Linear conversation flow with negative logic (NO LLM - 0ms, $0 cost)
"""

from audio_manager import audio_manager

class SmartRouter:
    """Handles INSTANT response selection using conversation flow + negative logic"""
    
    def __init__(self):
        self.setup_patterns()
        print("⚡ Smart Router initialized: LINEAR FLOW + NEGATIVE LOGIC mode (0ms, $0 cost)")
    
    def setup_patterns(self):
        """Setup conversation flow patterns"""
        
        # 🚫 UNIVERSAL NEGATIVE KEYWORDS (Always check these first)
        self.negative_keywords = [
            # Hindi
            "नहीं", "नही", "बाद में", "बिजी", "समय नहीं", "रुचि नहीं", "चाहिए नहीं",
            
            # English  
            "no", "nahi", "not interested", "busy", "later", "call back", 
            "don't need", "not now", "time nahi", "bye", "hang up",
            
            # Mixed
            "not चाहिए", "busy हूं", "time नहीं है", "later call करो"
        ]
        
        # 💰 HIGH-PRIORITY SPECIFIC INTENTS (Check these before general flow)
        self.specific_intents = {
            # Pricing (highest priority)
            "pricing_keywords": [
                "price", "pricing", "cost", "fees", "charges", "rate", "budget",
                "प्राइस", "प्राइसिंग", "कॉस्ट", "फीस", "पैसा", "बजट", "खर्चा",
                "how much", "kitna", "amount"
            ],
            "pricing_response": "klariqo_pricing.mp3 + 3000_mins_breakdown.mp3 + 40_calls_everymonth.mp3",
            
            # Demo requests
            "demo_keywords": [
                "demo", "meeting", "show", "dekhaiye", "दिखाओ", "demonstrate"
            ],
            "demo_response": "glad_for_demo_and_patent_mention.mp3 + meeting_with_founder.mp3",
            
            # Technical questions
            "technical_keywords": [
                "how does it work", "setup", "technical", "कैसे काम", "install"
            ],
            "technical_response": "how_does_it_work_tech.mp3 + klariqo_adding_extra_features.mp3",
            
            # Receptionist objection
            "receptionist_keywords": [
                "already have", "team hai", "staff है", "receptionist है"
            ],
            "receptionist_response": "agents_need_no_breaks.mp3 + klariqo_concurrent_calls.mp3",
            
            # AI voice concern
            "ai_voice_keywords": [
                "computer voice", "artificial", "AI voice", "robotic", "fake"
            ],
            "ai_voice_response": "klariqo_agents_sound_so_realistic.mp3 + klariqo_agents_sound_so_realistic2.mp3"
        }
        
        # 📋 CONVERSATION STAGES
        self.conversation_stages = {
            "post_intro": {
                "positive_response": "klariqo_provides_voice_agent1.mp3 + voice_agents_trained_details.mp3 + basically_agent_answers_parents.mp3 + agent_guides_onboarding_process.mp3",
                "negative_response": "I understand you're busy. Would you like me to call you at a better time?"
            },
            "after_explanation": {
                "default_followup": "What specific aspect would you like to know more about - our pricing, technical setup, or would you like to see a demo?"
            }
        }
        
        print(f"📝 Smart patterns loaded:")
        print(f"   - Negative keywords: {len(self.negative_keywords)}")
        print(f"   - Specific intents: {len(self.specific_intents) // 2}")  # Each intent has keywords + response
        print(f"   - Conversation stages: {len(self.conversation_stages)}")
    
    def detect_specific_intent(self, user_input):
        """Check for high-priority specific intents first"""
        user_lower = user_input.lower().strip()
        
        # Check pricing
        if any(kw in user_lower for kw in self.specific_intents["pricing_keywords"]):
            print(f"💰 PRICING INTENT: {user_input}")
            return "AUDIO", self.specific_intents["pricing_response"]
        
        # Check demo
        if any(kw in user_lower for kw in self.specific_intents["demo_keywords"]):
            print(f"🎬 DEMO INTENT: {user_input}")
            return "AUDIO", self.specific_intents["demo_response"]
        
        # Check technical
        if any(kw in user_lower for kw in self.specific_intents["technical_keywords"]):
            print(f"🔧 TECHNICAL INTENT: {user_input}")
            return "AUDIO", self.specific_intents["technical_response"]
        
        # Check receptionist objection
        if any(kw in user_lower for kw in self.specific_intents["receptionist_keywords"]):
            print(f"👥 RECEPTIONIST OBJECTION: {user_input}")
            return "AUDIO", self.specific_intents["receptionist_response"]
        
        # Check AI voice concern
        if any(kw in user_lower for kw in self.specific_intents["ai_voice_keywords"]):
            print(f"🤖 AI VOICE CONCERN: {user_input}")
            return "AUDIO", self.specific_intents["ai_voice_response"]
        
        return None, None
    
    def is_negative_response(self, user_input):
        """Check if user response is negative"""
        user_lower = user_input.lower().strip()
        return any(neg in user_lower for neg in self.negative_keywords)
    
    def get_conversation_stage(self, session):
        """Determine what stage of conversation we're in"""
        if not hasattr(session, 'conversation_history') or len(session.conversation_history) == 0:
            return "post_intro"
        
        # Check if we've already given the main explanation
        for entry in session.conversation_history:
            if "klariqo_provides_voice_agent1.mp3" in entry:
                return "after_explanation"
        
        return "post_intro"
    
    def handle_conversation_flow(self, user_input, conversation_stage):
        """Handle linear conversation flow based on stage"""
        
        if conversation_stage == "post_intro":
            # First response after intro - use negative logic
            if self.is_negative_response(user_input):
                print(f"🚫 NEGATIVE RESPONSE (Post-Intro): {user_input}")
                return "TTS", self.conversation_stages["post_intro"]["negative_response"]
            else:
                print(f"✅ POSITIVE RESPONSE (Post-Intro): {user_input}")
                return "AUDIO", self.conversation_stages["post_intro"]["positive_response"]
        
        elif conversation_stage == "after_explanation":
            # After main explanation - check for negatives, otherwise ask for clarification
            if self.is_negative_response(user_input):
                print(f"🚫 NEGATIVE RESPONSE (After Explanation): {user_input}")
                return "TTS", "I understand. Would you like me to send you some information via WhatsApp instead?"
            else:
                print(f"❓ UNCLEAR INTENT (After Explanation): {user_input}")
                return "TTS", self.conversation_stages["after_explanation"]["default_followup"]
        
        # Default fallback
        return "TTS", "I want to help you in the best way possible. Could you tell me what specific aspect you'd like to know more about?"
    
    def get_school_response(self, user_input, session):
        """Get response using LINEAR FLOW + NEGATIVE LOGIC (0ms, $0)"""
        
        # PRIORITY 1: Check for specific intents first (pricing, demo, technical, etc.)
        response_type, content = self.detect_specific_intent(user_input)
        if response_type:
            return response_type, content
        
        # PRIORITY 2: Handle conversation flow based on stage
        conversation_stage = self.get_conversation_stage(session)
        response_type, content = self.handle_conversation_flow(user_input, conversation_stage)
        if response_type:
            return response_type, content
        
        # PRIORITY 3: Default fallback
        return "TTS", "I want to help you in the best way possible. Could you tell me what specific aspect you'd like to know more about?"
    
    def validate_response(self, response_content):
        """Validate that the response contains valid audio files"""
        if not response_content or response_content.startswith("GENERATE:"):
            return True
        
        # Validate audio chain
        return audio_manager.validate_audio_chain(response_content)
    
    def get_stats(self):
        """Get smart router statistics"""
        return {
            "negative_keywords": len(self.negative_keywords),
            "specific_intents": len(self.specific_intents) // 2,
            "conversation_stages": len(self.conversation_stages),
            "cost_per_response": 0,
            "latency_ms": 0,
            "approach": "Linear Flow + Negative Logic"
        }

# Global smart router instance
smart_router = SmartRouter()