#!/usr/bin/env python3
"""
KLARIQO AUDIO OPTIMIZER
Converts all MP3 files to ultra-compressed versions for faster loading
"""

import os
import subprocess
import time

def optimize_audio_files():
    """Convert all audio files to ultra-compressed versions"""
    
    input_folder = "audio/"
    output_folder = "audio_optimised_script/"
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found!")
        print("📥 Install ffmpeg:")
        print("   Windows: Download from https://ffmpeg.org/download.html")
        print("   Mac: brew install ffmpeg") 
        print("   Linux: sudo apt install ffmpeg")
        return False
    
    if not os.path.exists(input_folder):
        print(f"❌ Input folder '{input_folder}' not found!")
        print(f"💡 Create the folder and add your original MP3 files")
        return False
    
    # Get list of MP3 files
    mp3_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.mp3')]
    
    if not mp3_files:
        print(f"❌ No MP3 files found in '{input_folder}'")
        return False
    
    print(f"🎵 Found {len(mp3_files)} MP3 files to optimize")
    print("🚀 Starting ultra-compression...")
    print("⚡ Settings: 32 kbps, mono, 22kHz (perfect for voice calls)")
    print()
    
    successful = 0
    failed = 0
    total_size_before = 0
    total_size_after = 0
    
    for i, filename in enumerate(mp3_files, 1):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        # Get original file size
        original_size = os.path.getsize(input_path)
        total_size_before += original_size
        
        print(f"[{i}/{len(mp3_files)}] Processing: {filename} ({original_size // 1024} KB)")
        
        try:
            # Ultra-aggressive compression for voice calls
            subprocess.run([
                'ffmpeg', 
                '-i', input_path,           # Input file
                '-b:a', '32k',              # 32 kbps bitrate
                '-ac', '1',                 # Mono (single channel)
                '-ar', '22050',             # 22kHz sample rate
                '-f', 'mp3',                # MP3 format
                '-y',                       # Overwrite output files
                output_path
            ], check=True, capture_output=True)
            
            # Get compressed file size
            compressed_size = os.path.getsize(output_path)
            total_size_after += compressed_size
            compression_ratio = ((original_size - compressed_size) / original_size) * 100
            
            print(f"   ✅ {compressed_size // 1024} KB ({compression_ratio:.1f}% smaller)")
            successful += 1
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
    
    print()
    print("=" * 50)
    print("🎯 OPTIMIZATION COMPLETE!")
    print(f"✅ Successfully optimized: {successful} files")
    if failed > 0:
        print(f"❌ Failed: {failed} files")
    
    if total_size_before > 0:
        total_compression = ((total_size_before - total_size_after) / total_size_before) * 100
        print(f"📊 Total size reduction: {total_compression:.1f}%")
        print(f"📁 Before: {total_size_before // 1024} KB")
        print(f"📁 After:  {total_size_after // 1024} KB")
        print(f"⚡ Saved:  {(total_size_before - total_size_after) // 1024} KB")
    
    print()
    print(f"📂 Optimized files are in: {output_folder}")
    print("🚀 Your Klariqo system will now load audio files lightning fast!")
    
    return successful > 0

def test_sample_file():
    """Test compression on a single file"""
    input_folder = "audio/"
    output_folder = "audio_optimised/"
    
    mp3_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.mp3')]
    
    if mp3_files:
        test_file = mp3_files[0]
        print(f"🧪 Testing compression on: {test_file}")
        
        input_path = os.path.join(input_folder, test_file)
        output_path = os.path.join(output_folder, f"test_{test_file}")
        
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            subprocess.run([
                'ffmpeg', '-i', input_path,
                '-b:a', '32k', '-ac', '1', '-ar', '22050',
                '-y', output_path
            ], check=True, capture_output=True)
            
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            ratio = ((original_size - compressed_size) / original_size) * 100
            
            print(f"📊 Original: {original_size // 1024} KB")
            print(f"📊 Compressed: {compressed_size // 1024} KB")
            print(f"📊 Reduction: {ratio:.1f}%")
            print(f"🎵 Test file saved as: {output_path}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 KLARIQO AUDIO OPTIMIZER")
    print("=" * 50)
    
    choice = input("Choose option:\n1. Optimize all files\n2. Test on one file\n> ").strip()
    
    if choice == "1":
        optimize_audio_files()
    elif choice == "2":
        test_sample_file()
    else:
        print("❌ Invalid choice")