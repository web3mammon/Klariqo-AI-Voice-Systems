#!/usr/bin/env python3
"""
KLARIQO AUDIO MANAGEMENT MODULE - PCM VERSION
Handles loading, caching, and serving of PCM audio files (pre-converted for Exotel)
"""

import os
import json
from flask import Response
from config import Config

class AudioManager:
    """Manages PCM audio file library and serving with ULTRA-FAST memory caching"""
    
    def __init__(self):
        self.audio_folder = "audio_pcm"  # Changed to PCM folder
        self.audio_snippets = self._load_audio_snippets()
        self.cached_files = set()
        self.memory_cache = {}  # 🚀 IN-MEMORY PCM FILE CACHE
        self._cache_loaded = False  # Prevent double loading
    
    def _load_audio_snippets(self):
        """Load audio snippets configuration from JSON file"""
        try:
            with open('audio_snippets.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ audio_snippets.json not found, using empty library")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing audio_snippets.json: {e}")
            return {}
    
    def _load_all_files_into_memory(self):
        """🚀 LOAD ALL PCM FILES INTO RAM FOR INSTANT SERVING"""
        # FIXED: Only load once
        if self._cache_loaded:
            return
            
        if not os.path.exists(self.audio_folder):
            os.makedirs(self.audio_folder, exist_ok=True)
            print(f"📁 Created PCM folder: {self.audio_folder}")
        
        # Get all audio files referenced in the JSON (but look for .pcm versions)
        all_files = set()
        for category, files in self.audio_snippets.items():
            if category == "quick_responses":
                for filename in files.values():
                    # Convert MP3 filename to PCM filename
                    pcm_filename = filename.replace('.mp3', '.pcm')
                    all_files.add(pcm_filename)
            else:
                for filename in files.keys():
                    # Convert MP3 filename to PCM filename
                    pcm_filename = filename.replace('.mp3', '.pcm')
                    all_files.add(pcm_filename)
        
        # Load PCM files directly into memory
        loaded_count = 0
        missing_count = 0
        total_size = 0
        
        for pcm_filename in all_files:
            file_path = os.path.join(self.audio_folder, pcm_filename)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        pcm_data = f.read()
                    
                    # Store original MP3 filename as key (for compatibility)
                    mp3_filename = pcm_filename.replace('.pcm', '.mp3')
                    self.memory_cache[mp3_filename] = pcm_data
                    self.cached_files.add(mp3_filename)
                    
                    loaded_count += 1
                    total_size += len(pcm_data)
                        
                except Exception as e:
                    print(f"❌ Failed to cache {pcm_filename}: {e}")
                    missing_count += 1
            else:
                print(f"⚠️ Missing PCM file: {pcm_filename}")
                missing_count += 1
        
        # Simple summary only
        size_mb = total_size / (1024 * 1024)
        print(f"🎵 PCM cache: {loaded_count} files loaded ({size_mb:.1f}MB)")
        if missing_count > 0:
            print(f"⚠️ {missing_count} PCM files missing")
        
        # Mark as loaded to prevent double loading
        self._cache_loaded = True
    
    def get_audio_library_for_prompt(self):
        """Get formatted audio library for AI prompt"""
        prompt_text = "Available audio files:\n\n"
        
        for category, files in self.audio_snippets.items():
            if category == "quick_responses":
                continue  # Skip quick responses in main prompt
            
            # Format category name
            category_name = category.replace("_", " ").title()
            prompt_text += f"# {category_name.upper()}\n"
            
            for filename, transcript in files.items():
                prompt_text += f"{filename} | {transcript}\n"
            
            prompt_text += "\n"
        
        return prompt_text
    
    def get_quick_response(self, user_input):
        """Check if user input matches any quick response patterns"""
        user_lower = user_input.lower()
        quick_responses = self.audio_snippets.get("quick_responses", {})
        
        for phrase, filename in quick_responses.items():
            if phrase in user_lower:
                print(f"⚡ QUICK RESPONSE CACHE HIT: '{phrase}' → {filename}")
                return filename
        
        return None
    
    def serve_audio_file(self, filename):
        """🚀 SERVE PCM FILE FROM MEMORY CACHE (ULTRA-FAST!)"""
        if filename in self.memory_cache:
            # Serve PCM data directly from memory - INSTANT!
            pcm_data = self.memory_cache[filename]
            
            return Response(
                pcm_data,
                mimetype='application/octet-stream',  # Raw binary data
                headers={
                    'Content-Length': str(len(pcm_data)),
                    'Cache-Control': 'public, max-age=3600',
                    'Accept-Ranges': 'bytes',
                    'X-Served-From': 'memory-cache-pcm'  # Debug header
                }
            )
        else:
            print(f"❌ PCM file not in memory cache: {filename}")
            return Response("PCM file not found in cache", status=404)
    
    def validate_audio_chain(self, audio_chain):
        """Validate that all PCM files in an audio chain exist in memory cache"""
        if not audio_chain:
            return False
        
        files = [f.strip() for f in audio_chain.split('+')]
        missing_files = []
        
        for filename in files:
            if filename not in self.memory_cache:
                missing_files.append(filename)
        
        if missing_files:
            print(f"⚠️ Missing PCM files in chain: {missing_files}")
            return False
        
        return True
    
    def get_file_info(self, filename):
        """Get transcript and category info for a file"""
        for category, files in self.audio_snippets.items():
            if category == "quick_responses":
                continue
            
            if filename in files:
                return {
                    'filename': filename,
                    'transcript': files[filename],
                    'category': category,
                    'exists': filename in self.cached_files,
                    'cached_in_memory': filename in self.memory_cache,
                    'size_kb': len(self.memory_cache.get(filename, b'')) // 1024,
                    'format': 'PCM (16-bit, 8kHz, mono)'
                }
        
        return None
    
    def get_memory_stats(self):
        """Get detailed memory cache statistics for PCM files"""
        total_size = sum(len(data) for data in self.memory_cache.values())
        
        return {
            'cached_files': len(self.memory_cache),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'files_list': list(self.memory_cache.keys()),
            'average_file_size_kb': (total_size // 1024) // len(self.memory_cache) if self.memory_cache else 0,
            'format': 'PCM direct (no conversion needed)'
        }
    
    def clear_memory_cache(self):
        """🗑️ Clear PCM memory cache (called on shutdown)"""
        cache_size_mb = sum(len(data) for data in self.memory_cache.values()) / (1024 * 1024)
        file_count = len(self.memory_cache)
        
        self.memory_cache.clear()
        
        print(f"🗑️ PCM memory cache cleared: {file_count} files, {cache_size_mb:.1f}MB freed")
    
    def get_pcm_data(self, filename):
        """Get raw PCM data for a file from memory cache (ready for Exotel)"""
        return self.memory_cache.get(filename)
    
    def add_audio_file(self, filename, transcript, category):
        """Add new audio file to library (for future dynamic updates)"""
        if category not in self.audio_snippets:
            self.audio_snippets[category] = {}
        
        self.audio_snippets[category][filename] = transcript
        
        # Save updated library
        with open('audio_snippets.json', 'w', encoding='utf-8') as f:
            json.dump(self.audio_snippets, f, indent=2, ensure_ascii=False)
        
        # Try to load new PCM file into memory cache
        pcm_filename = filename.replace('.mp3', '.pcm')
        file_path = os.path.join(self.audio_folder, pcm_filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    pcm_data = f.read()
                self.memory_cache[filename] = pcm_data  # Use MP3 name as key
                self.cached_files.add(filename)
                print(f"➕ Added and cached PCM: {filename} ({len(pcm_data) // 1024}KB)")
            except Exception as e:
                print(f"➕ Added to library but failed to cache PCM: {filename} - {e}")
        else:
            print(f"➕ Added to library: {filename} (PCM file not found for caching)")
    
    def list_all_files(self):
        """List all PCM audio files with their memory cache status"""
        all_files = []
        
        for category, files in self.audio_snippets.items():
            if category == "quick_responses":
                continue
            
            for filename, transcript in files.items():
                file_info = {
                    'filename': filename,
                    'transcript': transcript[:50] + "..." if len(transcript) > 50 else transcript,
                    'category': category,
                    'exists': filename in self.cached_files,
                    'cached_in_memory': filename in self.memory_cache,
                    'format': 'PCM'
                }
                
                if filename in self.memory_cache:
                    file_info['size_kb'] = len(self.memory_cache[filename]) // 1024
                
                all_files.append(file_info)
        
        return sorted(all_files, key=lambda x: x['filename'])
    
    def reload_library(self):
        """Reload audio snippets and refresh PCM memory cache"""
        # Only load if not already loaded
        if not self._cache_loaded:
            self._load_all_files_into_memory()
    
    def __del__(self):
        """Cleanup method called when object is destroyed"""
        if hasattr(self, 'memory_cache') and self.memory_cache:
            self.clear_memory_cache()

# Global audio manager instance
audio_manager = AudioManager()