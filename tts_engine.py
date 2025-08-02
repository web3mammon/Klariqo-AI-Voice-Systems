#!/usr/bin/env python3
"""
KLARIQO TEXT-TO-SPEECH ENGINE MODULE
Handles ElevenLabs TTS for dynamic content generation
"""

import os
import time
from elevenlabs import ElevenLabs, VoiceSettings
from config import Config

class TTSEngine:
    """Manages text-to-speech generation using ElevenLabs"""
    
    def __init__(self):
        self.client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        self.voice_id = Config.VOICE_ID
        self.temp_folder = Config.TEMP_FOLDER
        
        # Ensure temp folder exists
        os.makedirs(self.temp_folder, exist_ok=True)
    
    def generate_audio(self, text, save_temp=True):
        """
        Generate audio from text using ElevenLabs
        
        Args:
            text (str): Text to convert to speech
            save_temp (bool): Whether to save as temporary file
            
        Returns:
            str: Path to generated audio file, or None if failed
        """
        try:
            # Configure voice settings for natural speech
            voice_settings = VoiceSettings(
                stability=0.5,        # Balanced stability
                similarity_boost=0.8, # High similarity to original voice
                style=0.0,           # Neutral style
                use_speaker_boost=False
            )
            
            # Generate audio stream
            audio_stream = self.client.text_to_speech.stream(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_flash_v2_5",  # Fast model for real-time
                voice_settings=voice_settings
            )
            
            # Collect audio data
            audio_data = b""
            for chunk in audio_stream:
                if chunk:
                    audio_data += chunk
            
            if not audio_data:
                return None
            
            if save_temp:
                # Save to temporary file
                timestamp = int(time.time())
                temp_filename = f"temp_tts_{timestamp}.mp3"
                temp_path = os.path.join(self.temp_folder, temp_filename)
                
                with open(temp_path, 'wb') as f:
                    f.write(audio_data)
                
                return temp_filename
            else:
                # Return raw audio data
                return audio_data
                
        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            return None
    
    def generate_audio_url(self, text, base_url):
        """
        Generate TTS audio and return URL for Twilio
        
        Args:
            text (str): Text to convert
            base_url (str): Base URL for serving files
            
        Returns:
            str: Full URL to generated audio file, or None if failed
        """
        temp_filename = self.generate_audio(text, save_temp=True)
        
        if temp_filename:
            # TTS files are served from /temp/ route (temp folder)
            return f"{base_url}/temp/{temp_filename}"
        else:
            return None
    
    def cleanup_temp_files(self, max_age_hours=1):
        """
        Clean up old temporary TTS files
        
        Args:
            max_age_hours (int): Maximum age in hours before deletion
        """
        if not os.path.exists(self.temp_folder):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        try:
            for filename in os.listdir(self.temp_folder):
                if filename.startswith("temp_tts_") and filename.endswith(".mp3"):
                    file_path = os.path.join(self.temp_folder, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
            
            if cleaned_count > 0:
                print(f"🗑️ Cleaned up {cleaned_count} old TTS files")
                
        except Exception as e:
            print(f"⚠️ Error during TTS cleanup: {e}")
    
    def test_voice(self, test_text="Hello, this is a test of the Klariqo TTS system."):
        """
        Test TTS functionality
        
        Args:
            test_text (str): Text to use for testing
            
        Returns:
            bool: True if test successful, False otherwise
        """
        print("🧪 Testing TTS engine...")
        
        result = self.generate_audio(test_text, save_temp=False)
        
        if result:
            print("✅ TTS test successful")
            return True
        else:
            print("❌ TTS test failed")
            return False
    
    def get_voice_info(self):
        """Get information about the current voice"""
        try:
            voices = self.client.voices.get_all()
            for voice in voices.voices:
                if voice.voice_id == self.voice_id:
                    return {
                        'name': voice.name,
                        'voice_id': voice.voice_id,
                        'category': voice.category,
                        'description': getattr(voice, 'description', 'No description')
                    }
            return None
        except Exception as e:
            print(f"⚠️ Could not fetch voice info: {e}")
            return None

# Global TTS engine instance
tts_engine = TTSEngine()