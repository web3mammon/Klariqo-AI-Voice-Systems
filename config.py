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
    
    # ElevenLabs Voice Settings
    VOICE_ID = "TRnaQb7q41oL7sV0w6Bu"  # Nisha's voice
    
    # Deepgram Settings
    DEEPGRAM_MODEL = "nova-2"
    DEEPGRAM_LANGUAGE = "hi"  # Hindi + English mix
    
    # Session Settings
    SILENCE_THRESHOLD = 0.4  # seconds before considering speech complete
    
    # Flask Settings
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    FLASK_DEBUG = False
    
    # File Paths
    AUDIO_FOLDER = "audio_optimised/"
    LOGS_FOLDER = "logs/"
    TEMP_FOLDER = "temp/"
    
    # Call Campaign Settings
    MAX_CONCURRENT_CALLS = 50
    CALL_INTERVAL = 10  # seconds between outbound calls
    
    # Session Memory Flags Template
    SESSION_FLAGS_TEMPLATE = {
        "intro_played": False,
        "klariqo_explained": False, 
        "features_discussed": False,
        "pricing_mentioned": False,
        "demo_offered": False,
        "meeting_scheduled": False
    }
    
    @classmethod
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            'DEEPGRAM_API_KEY',
            'GEMINI_API_KEY', 
            'ELEVENLABS_API_KEY',
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'TWILIO_PHONE'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Validate configuration on import
Config.validate_config()