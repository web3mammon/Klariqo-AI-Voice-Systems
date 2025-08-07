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
        print(f"   - Filename (e.g., school_intro.mp3)")
        print(f"   - Transcript (Hindi/English text)")
        print(f"   - Category (optional - will auto-detect):")
        print(f"     * introductions")
        print(f"     * school_info")
        print(f"     * admission_process")
        print(f"     * fees_and_pricing")
        print(f"     * school_facilities")
        print(f"     * transport_and_bus")
        print(f"     * school_activities")
        print(f"     * school_events")
        print(f"     * conclusion")
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
            "school_info": {},
            "admission_process": {},
            "fees_and_pricing": {},
            "school_facilities": {},
            "transport_and_bus": {},
            "school_activities": {},
            "school_events": {},
            "conclusion": {},
            "miscellaneous": {},
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
    """Smart guess category based on filename for school content"""
    filename_lower = filename.lower()
    
    # Person introduction files (Nisha introducing herself)
    if any(word in filename_lower for word in ["nisha_intro", "nisha_introduction"]):
        return "introductions"
    
    # School information files (when user asks about the school)
    elif any(word in filename_lower for word in ["school_intro"]):
        return "school_info"
    
    # Admission process files
    elif any(word in filename_lower for word in ["admission", "process", "form", "transfer", "firsttime", "last_date"]):
        return "admission_process"
    
    # Fees and pricing files
    elif any(word in filename_lower for word in ["fees", "pricing", "cost", "charges", "scholarship", "discount"]):
        return "fees_and_pricing"
    
    # School facilities files
    elif any(word in filename_lower for word in ["smart", "cctv", "security", "cbse", "classroom"]):
        return "school_facilities"
    
    # Transport and bus files
    elif any(word in filename_lower for word in ["bus", "transport", "location", "route"]):
        return "transport_and_bus"
    
    # School activities files
    elif any(word in filename_lower for word in ["activities", "sports", "music", "dance", "extra"]):
        return "school_activities"
    
    # School events files
    elif any(word in filename_lower for word in ["event", "function", "annual", "celebration"]):
        return "school_events"
    
    # Conclusion and goodbye files
    elif any(word in filename_lower for word in ["goodbye", "thank", "conclusion"]):
        return "conclusion"
    
    # Timings and general info
    elif any(word in filename_lower for word in ["timing", "time", "schedule", "ji_bilkul"]):
        return "miscellaneous"
    
    else:
        return "miscellaneous"

def create_sample_excel():
    """Create a sample Excel file with the right structure for school content"""
    sample_data = {
        'Filename': [
            'nisha_intro.mp3',
            'school_intro.mp3',
            'admission_process_firsttime.mp3',
            'fees_ask_class.mp3',
            'smart_classes.mp3',
            'bus_fees.mp3',
            'extra_activities.mp3',
            'annual_function_invite.mp3',
            'thank_you_goodbye.mp3'
        ],
        'Transcript': [
            'Namaste! AVS International School se mai Nisha bol rahi hu.',
            'AVS International एक modern CBSE-affiliated school है, जो academic excellence के साथ-साथ बच्चों के holistic development पर भी focus करता है।',
            'जी बिल्कुल! आप स्कूल से admission form प्राप्त कर सकते हैं या हमारी website से download कर सकते हैं।',
            'बिल्कुल! Fees के बारे में, क्या मैं आपके बच्चे के admission की class के बारे में जान सक्ती हूँ?',
            'Ofcourse! Classrooms smart boards से equipped हैं, जिससे पढ़ाई interactive और engaging होती है।',
            'जी bus की fees लगभग 500 से 800 रुपये होती है, लेकिन आप इसे और confirm करने के लिए एक बार school आके बात कर लीजिये।',
            'हमारे school में music, dance, football, basketball और skating जैसी कई activities होती हैं।',
            'Fantastic! Actually, मैंने आपको यह बताने के लिए call किया था कि AVS International, 18 september को अपना annual function host कर रहा है।',
            'Ofcourse! कभी भी आपको कोई aur doubt हो या सवाल हो तो कॉल कर लीजिएगा। Thank you for calling AVS International.'
        ],
        'Category': [
            'introductions',
            'school_info',
            'admission_process', 
            'fees_and_pricing',
            'school_facilities',
            'transport_and_bus',
            'school_activities',
            'school_events',
            'conclusion'
        ],
        'Alternate_Version': [
            'nisha_introduction_outbound.mp3',
            '',
            'admission_process_transfer.mp3',
            '',
            '',
            'bus_ask_location.mp3',
            '',
            'annual_function_events.mp3',
            ''
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