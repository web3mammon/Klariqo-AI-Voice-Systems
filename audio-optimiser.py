#!/usr/bin/env python3
"""
KLARIQO PCM AUDIO CONVERTER
Converts all MP3 files to PCM format for Exotel (16-bit, 8kHz, mono)
Uses librosa for reliable MP3 decoding without external dependencies
"""

import os
import time
import numpy as np
import librosa
from pathlib import Path

def install_requirements():
    """Install required packages if not available"""
    try:
        import librosa
        import numpy
        print("✅ Required packages available")
        return True
    except ImportError:
        print("📦 Installing required packages...")
        try:
            import subprocess
            subprocess.check_call(["pip", "install", "librosa", "numpy"])
            print("✅ Packages installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install packages: {e}")
            print("💡 Please run manually: pip install librosa numpy")
            return False

def convert_mp3_to_pcm_file(mp3_path, pcm_path):
    """
    Convert a single MP3 file to PCM format (16-bit, 8kHz, mono)
    Returns: (success, original_size_kb, pcm_size_kb)
    """
    try:
        # Get original file size
        original_size = os.path.getsize(mp3_path)
        
        # Load MP3 with librosa - automatically converts to the format we need
        audio_data, sample_rate = librosa.load(mp3_path, sr=8000, mono=True)
        
        print(f"   📊 Loaded: 8000Hz, mono, {len(audio_data)} samples")
        
        # Convert to 16-bit PCM
        # Clip to [-1, 1] range and scale to 16-bit integer
        audio_data = np.clip(audio_data, -1.0, 1.0)
        pcm_16bit = (audio_data * 32767).astype(np.int16)
        
        # Save as raw PCM file (binary data)
        with open(pcm_path, 'wb') as f:
            f.write(pcm_16bit.tobytes())
        
        # Get PCM file size
        pcm_size = os.path.getsize(pcm_path)
        
        # Calculate compression stats
        original_size_kb = original_size // 1024
        pcm_size_kb = pcm_size // 1024
        
        print(f"   ✅ {original_size_kb} KB MP3 → {pcm_size_kb} KB PCM")
        
        return True, original_size_kb, pcm_size_kb
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False, 0, 0

def convert_all_mp3_to_pcm():
    """Convert all MP3 files to PCM format"""
    
    input_folders = ["audio_optimised/inbound", "audio_optimised/outbound"]
    output_folder = "audio_pcm"
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Collect MP3 files from both inbound and outbound folders
    mp3_files = []
    for input_folder in input_folders:
        if not os.path.exists(input_folder):
            print(f"⚠️ Input folder '{input_folder}' not found, skipping...")
            continue
        
        folder_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith('.mp3')]
        mp3_files.extend(folder_files)
    
    if not mp3_files:
        print(f"❌ No MP3 files found in input folders")
        return False
    
    print(f"🎵 Found {len(mp3_files)} MP3 files to convert")
    print("🔄 Converting to PCM format (16-bit, 8kHz, mono)")
    print("⚡ Perfect for Exotel's 320-byte chunking requirement")
    print()
    
    successful = 0
    failed = 0
    total_mp3_size = 0
    total_pcm_size = 0
    
    for i, mp3_path in enumerate(mp3_files, 1):
        filename = os.path.basename(mp3_path)
        pcm_filename = filename.replace('.mp3', '.pcm')
        pcm_path = os.path.join(output_folder, pcm_filename)
        
        print(f"[{i}/{len(mp3_files)}] Converting: {filename}")
        
        success, mp3_kb, pcm_kb = convert_mp3_to_pcm_file(mp3_path, pcm_path)
        
        if success:
            successful += 1
            total_mp3_size += mp3_kb
            total_pcm_size += pcm_kb
            
            # Verify PCM can be chunked properly
            pcm_size_bytes = os.path.getsize(pcm_path)
            chunks_possible = pcm_size_bytes // 320
            print(f"   📊 Can create {chunks_possible} chunks of 320 bytes")
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print("🎯 PCM CONVERSION COMPLETE!")
    print(f"✅ Successfully converted: {successful} files")
    if failed > 0:
        print(f"❌ Failed: {failed} files")
    
    if total_mp3_size > 0:
        print(f"📊 Total MP3 size: {total_mp3_size} KB")
        print(f"📊 Total PCM size: {total_pcm_size} KB")
        if total_pcm_size > total_mp3_size:
            print(f"📈 PCM is {((total_pcm_size - total_mp3_size) / total_mp3_size * 100):.1f}% larger (uncompressed)")
        else:
            print(f"📉 PCM is {((total_mp3_size - total_pcm_size) / total_mp3_size * 100):.1f}% smaller")
    
    print()
    print(f"📂 PCM files saved in: {output_folder}")
    print("🚀 Your Klariqo system can now load PCM files for instant playback!")
    print()
    print("💡 Next steps:")
    print("   1. Update audio_manager.py to load .pcm files")
    print("   2. Skip MP3→PCM conversion in main.py")
    print("   3. Send PCM data directly to Exotel")
    
    return successful > 0

def test_single_conversion():
    """Test conversion on a single file"""
    input_folder = "audio_optimised"
    output_folder = "audio_pcm_test"
    
    if not os.path.exists(input_folder):
        print(f"❌ Input folder '{input_folder}' not found!")
        return
    
    mp3_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.mp3')]
    
    if not mp3_files:
        print(f"❌ No MP3 files found in '{input_folder}'")
        return
    
    test_file = mp3_files[0]
    print(f"🧪 Testing PCM conversion on: {test_file}")
    
    os.makedirs(output_folder, exist_ok=True)
    
    mp3_path = os.path.join(input_folder, test_file)
    pcm_filename = test_file.replace('.mp3', '.pcm')
    pcm_path = os.path.join(output_folder, f"test_{pcm_filename}")
    
    success, mp3_kb, pcm_kb = convert_mp3_to_pcm_file(mp3_path, pcm_path)
    
    if success:
        print()
        print("✅ Test conversion successful!")
        print(f"📁 Test PCM file: {pcm_path}")
        
        # Verify chunking
        pcm_size_bytes = os.path.getsize(pcm_path)
        chunks_possible = pcm_size_bytes // 320
        remaining_bytes = pcm_size_bytes % 320
        
        print(f"📊 PCM file size: {pcm_size_bytes} bytes")
        print(f"📊 320-byte chunks: {chunks_possible}")
        if remaining_bytes > 0:
            print(f"📊 Remaining bytes: {remaining_bytes} (will be padded)")
        
        print("🎯 Ready for Exotel chunking!")
    else:
        print("❌ Test conversion failed")

def verify_exotel_compatibility():
    """Verify that converted PCM files are compatible with Exotel"""
    pcm_folder = "audio_pcm"
    
    if not os.path.exists(pcm_folder):
        print(f"❌ PCM folder '{pcm_folder}' not found!")
        print("💡 Run conversion first")
        return
    
    pcm_files = [f for f in os.listdir(pcm_folder) if f.lower().endswith('.pcm')]
    
    if not pcm_files:
        print(f"❌ No PCM files found in '{pcm_folder}'")
        return
    
    print("🔍 Verifying Exotel compatibility...")
    print()
    
    for filename in pcm_files[:5]:  # Check first 5 files
        pcm_path = os.path.join(pcm_folder, filename)
        file_size = os.path.getsize(pcm_path)
        
        # Calculate chunks
        full_chunks = file_size // 320
        remaining_bytes = file_size % 320
        
        print(f"📁 {filename}")
        print(f"   Size: {file_size} bytes")
        print(f"   Full 320-byte chunks: {full_chunks}")
        if remaining_bytes > 0:
            print(f"   Remaining bytes: {remaining_bytes} (needs padding)")
        print(f"   ✅ Compatible with Exotel")
        print()
    
    if len(pcm_files) > 5:
        print(f"... and {len(pcm_files) - 5} more files")
    
    print("🎯 All PCM files are ready for Exotel!")

if __name__ == "__main__":
    print("🚀 KLARIQO PCM AUDIO CONVERTER")
    print("=" * 60)
    print("Converts MP3 files to PCM format for Exotel")
    print("Format: 16-bit, 8kHz, mono (perfect for 320-byte chunks)")
    print()
    
    # Check and install requirements
    if not install_requirements():
        exit(1)
    
    print()
    choice = input("""Choose option:
1. Convert all MP3 files to PCM
2. Test conversion on one file
3. Verify Exotel compatibility
> """).strip()
    
    if choice == "1":
        convert_all_mp3_to_pcm()
    elif choice == "2":
        test_single_conversion()
    elif choice == "3":
        verify_exotel_compatibility()
    else:
        print("❌ Invalid choice")
    
    input("\nPress Enter to exit...")