#!/usr/bin/env python3
"""
KLARIQO EXCEL TO JSON CONVERTER
Reads audio file data from Excel and generates audio_snippets.json
"""

import os
import json
import pandas as pd

def excel_to_json():
    """Convert Excel file to audio_snippets.json"""
    
    excel_file = "audio_files.xlsx"  # Your Excel file name
    
    # Check if Excel file exists
    if not os.path.exists(excel_file):
        print(f"❌ Excel file '{excel_file}' not found!")
        print(f"💡 Create an Excel file with columns:")
        print(f"   - Filename")
        print(f"   - Transcript") 
        print(f"   - Category (optional)")
        print(f"   - Alternate_Version (optional)")
        return False
    
    try:
        # Read Excel file
        print(f"📖 Reading {excel_file}...")
        df = pd.read_excel(excel_file)
        
        # Show what columns we found
        print(f"📊 Columns found: {list(df.columns)}")
        print(f"📊 Total rows: {len(df)}")
        
        # Clean up column names (remove spaces, make lowercase)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Check required columns
        required_cols = ['filename', 'transcript']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            print(f"📋 Available columns: {list(df.columns)}")
            return False
        
        # Initialize the JSON structure
        audio_snippets = {
            "introductions": {},
            "klariqo_explanation": {},
            "key_features": {},
            "technical_concerns": {},
            "pricing": {},
            "demo_meeting": {},
            "ai_reveal_closing": {},
            "quick_responses": {}
        }
        
        # Process each row
        processed_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            filename = str(row['filename']).strip()
            transcript = str(row['transcript']).strip()
            
            # Skip empty rows
            if pd.isna(row['filename']) or pd.isna(row['transcript']):
                skipped_count += 1
                continue
            
            if filename == 'nan' or transcript == 'nan':
                skipped_count += 1
                continue
            
            # Ensure filename has .mp3 extension
            if not filename.endswith('.mp3'):
                filename += '.mp3'
            
            # Determine category (either from Excel or smart guess)
            if 'category' in df.columns and pd.notna(row['category']):
                category = str(row['category']).strip().lower().replace(' ', '_')
            else:
                # Smart category guessing
                category = guess_category(filename)
            
            # Make sure category exists in our structure
            if category not in audio_snippets:
                audio_snippets[category] = {}
            
            # Handle alternate versions - create separate entries
            if 'alternate_version' in df.columns and pd.notna(row['alternate_version']):
                alternate = str(row['alternate_version']).strip()
                if not alternate.endswith('.mp3'):
                    alternate += '.mp3'
                
                # Create separate entries for main file and alternate
                audio_snippets[category][filename] = transcript
                audio_snippets[category][alternate] = transcript + " [ALTERNATE VERSION]"
                print(f"✅ {filename} → {category}")
                print(f"✅ {alternate} → {category} (alternate)")
            else:
                # Single file entry
                audio_snippets[category][filename] = transcript
                print(f"✅ {filename} → {category}")
            
            processed_count += 1
        
        # Remove empty categories
        audio_snippets = {k: v for k, v in audio_snippets.items() if v}
        
        # Add quick responses (if they exist in Excel)
        if 'quick_phrase' in df.columns:
            quick_responses = {}
            for index, row in df.iterrows():
                if pd.notna(row.get('quick_phrase')) and pd.notna(row['filename']):
                    phrase = str(row['quick_phrase']).strip().lower()
                    filename = str(row['filename']).strip()
                    if not filename.endswith('.mp3'):
                        filename += '.mp3'
                    quick_responses[phrase] = filename
            
            if quick_responses:
                audio_snippets["quick_responses"] = quick_responses
        
        # Save to JSON file
        json_file = "audio_snippets.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(audio_snippets, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 SUCCESS!")
        print(f"📊 Processed: {processed_count} files")
        print(f"⚠️ Skipped: {skipped_count} empty rows")
        print(f"📁 Categories: {len(audio_snippets)}")
        print(f"💾 Saved to: {json_file}")
        
        # Show summary by category
        print(f"\n📋 Files per category:")
        for category, files in audio_snippets.items():
            if category != "quick_responses":
                print(f"   {category}: {len(files)} files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

def guess_category(filename):
    """Smart guess category based on filename"""
    filename_lower = filename.lower()
    
    if "intro" in filename_lower:
        return "introductions"
    elif any(word in filename_lower for word in ["pricing", "cost", "breakdown", "calls"]):
        return "pricing"
    elif any(word in filename_lower for word in ["demo", "meeting", "founder", "patent"]):
        return "demo_meeting"
    elif any(word in filename_lower for word in ["agent", "concurrent", "breaks", "realistic"]):
        return "key_features"
    elif any(word in filename_lower for word in ["tech", "wrong", "error", "stability"]):
        return "technical_concerns"
    elif any(word in filename_lower for word in ["provides", "voice", "trained", "basically"]):
        return "klariqo_explanation"
    elif any(word in filename_lower for word in ["goodbye", "mic_drop", "shocked"]):
        return "ai_reveal_closing"
    else:
        return "miscellaneous"

def create_sample_excel():
    """Create a sample Excel file with the right structure"""
    sample_data = {
        'Filename': [
            'intro_klariqo1.1.mp3',
            'klariqo_provides_voice_agent1.mp3',
            'agents_need_no_breaks.mp3',
            'klariqo_pricing1.1.mp3'
        ],
        'Transcript': [
            'नमस्ते! मैं निशा बोल रही हूं Klariqo से...',
            'बिलकुल ! तो Klariqo आपकी help करता है...',
            'इस एजेंट की सबसे खास बात यह है कि ये twenty four seven काम करते हैं',
            'हमने हमारी pricing का aim रखा है, to be as manageable for you as possible'
        ],
        'Category': [
            'introductions',
            'klariqo_explanation', 
            'key_features',
            'pricing'
        ],
        'Alternate_Version': [
            'intro_klariqo1.2.mp3',
            '',
            'best_feature_concurrent_call.mp3',
            'klariqo_pricing1.2.mp3'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    df.to_excel('audio_files_sample.xlsx', index=False)
    print("📝 Created sample Excel file: audio_files_sample.xlsx")

if __name__ == "__main__":
    print("🚀 KLARIQO EXCEL TO JSON CONVERTER")
    print("=" * 50)
    
    choice = input("Choose option:\n1. Convert Excel to JSON\n2. Create sample Excel\n> ").strip()
    
    if choice == "1":
        excel_to_json()
    elif choice == "2":
        create_sample_excel()
    else:
        print("❌ Invalid choice")