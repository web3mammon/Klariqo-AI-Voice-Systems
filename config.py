#!/usr/bin/env python3
"""
KLARIQO CONFIGURATION MODULE
Centralized configuration management for all API keys, constants, and settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration class for Klariqo"""
    
    # API Keys - loaded from environment variables
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY') 
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE = os.getenv('TWILIO_PHONE')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Exotel API Settings (Primary telephony provider for India)
    EXOTEL_ACCOUNT_SID = os.getenv('EXOTEL_ACCOUNT_SID')
    EXOTEL_API_TOKEN = os.getenv('EXOTEL_API_TOKEN')
    EXOTEL_PHONE = os.getenv('EXOTEL_PHONE')
    
    # ElevenLabs Voice Settings
    VOICE_ID = "TRnaQb7q41oL7sV0w6Bu"  # Nisha's voice - school receptionist
    
    # Deepgram Settings
    DEEPGRAM_MODEL = "nova-2"
    DEEPGRAM_LANGUAGE = "hi"  # Hindi + English mix for Indian school context
    
    # Session Settings
    SILENCE_THRESHOLD = 0.4  # seconds before considering speech complete
    
    # Flask Settings
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    FLASK_DEBUG = False
    
    # File Paths
    AUDIO_FOLDER = "audio_pcm/"
    LOGS_FOLDER = "logs/"
    TEMP_FOLDER = "temp/"
    
    # Call Campaign Settings
    MAX_CONCURRENT_CALLS = 50
    CALL_INTERVAL = 10  # seconds between outbound calls
    
    # Session Memory Flags Template for School Context
    SESSION_FLAGS_TEMPLATE = {
        "intro_played": False,
        "admission_process_explained": False, 
        "fees_discussed": False,
        "timings_mentioned": False,
        "documents_explained": False,
        "activities_discussed": False,
        "security_discussed": False,
        "transport_discussed": False,
        "age_eligibility_checked": False
    }
    
    # Dynamic Session Variables Template for Intelligent Responses
    SESSION_VARIABLES_TEMPLATE = {
        "admission_type": None,  # "firsttime" or "transfer"
        "admission_class": None,  # "KG1", "KG2", "Class 1", "Class 2", etc.
        "student_location": None,  # Location for bus route
        "student_age": None,  # Age for eligibility check
        "parent_name": None,  # Parent's name if mentioned
        "student_name": None,  # Student's name if mentioned
        "inquiry_focus": None  # "fees", "admission", "transport", "activities", etc.
    }
    
    @classmethod
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            'DEEPGRAM_API_KEY',
            'ELEVENLABS_API_KEY'
        ]
        
        # Optional: Either OpenAI, Groq, or Gemini for AI (at least one required)
        ai_apis = ['OPENAI_API_KEY', 'GROQ_API_KEY', 'GEMINI_API_KEY']
        if not any(getattr(cls, api) for api in ai_apis):
            raise ValueError("At least one AI API key required: OPENAI_API_KEY, GROQ_API_KEY, or GEMINI_API_KEY")
        
        # Optional: Either Twilio or Exotel for telephony (at least one required)
        telephony_apis = [
            ('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN'),
            ('EXOTEL_ACCOUNT_SID', 'EXOTEL_API_TOKEN')
        ]
        has_telephony = any(
            all(getattr(cls, api) for api in api_pair) 
            for api_pair in telephony_apis
        )
        if not has_telephony:
            raise ValueError("Either Twilio (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) or Exotel (EXOTEL_ACCOUNT_SID, EXOTEL_API_TOKEN) configuration required")
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Validate configuration on import
Config.validate_config()