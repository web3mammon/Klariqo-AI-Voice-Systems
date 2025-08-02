# 🔄 CLIENT ADAPTATION GUIDE
## Complete Steps to Adapt Klariqo System to New Industries

This guide provides **step-by-step instructions** to adapt the Klariqo voice agent system from the current **school/education industry** to any new industry (hotels, hospitals, restaurants, real estate, etc.).

---

## 📋 OVERVIEW: What Currently Needs Changing

**Current System:** Nisha (AI agent) calls school principals to sell Klariqo's voice agent services for handling student admissions and inquiries.

**Target Industries:** Hotels (reception), Hospitals (appointments), Restaurants (reservations), Real Estate (lead qualification), etc.

---

## 🎯 STEP-BY-STEP ADAPTATION PROCESS

### **PHASE 1: CONTENT PLANNING & STRATEGY**

#### 1.1 Define New Industry Context
**Required Actions:**
- [ ] **Identify target audience** (hotel managers, hospital administrators, restaurant owners)
- [ ] **Define pain points** specific to the industry
- [ ] **Research industry terminology** and common scenarios
- [ ] **Create conversation flow map** for the new industry

**Example for Hotels:**
```
Target: Hotel managers/owners
Pain Points: 
- Reception staff unavailable during peak check-in
- Multiple language requirements for international guests  
- 24/7 inquiry handling for bookings
- Cost of hiring multiple reception staff

Key Scenarios:
- Room availability inquiries
- Booking confirmations
- Amenity information
- Local area recommendations
- Complaint handling
```

#### 1.2 Script New Conversation Content
**Required Actions:**
- [ ] **Write new introduction script** (replace school context)
- [ ] **Create industry-specific feature explanations**
- [ ] **Develop pricing that makes sense** for the industry
- [ ] **Script objection handling** for industry-specific concerns
- [ ] **Plan demo/meeting approach** for the new audience

**Example for Hotels:**
```
Introduction: "Hi, this is Nisha from Klariqo. I have a 2-minute solution that's helping hotels like yours handle 3x more guest inquiries automatically, even during peak season..."

Features: 
- 24/7 guest service (no shift changes)
- Multi-language support for international guests
- Instant room availability checks
- Booking assistance and confirmations
- Concierge-style recommendations
```

---

### **PHASE 2: AUDIO CONTENT CREATION**

#### 2.1 Record New Audio Content
**Required Actions:**
- [ ] **Record new introduction audio** with industry context
- [ ] **Record feature explanation audios** for the new industry
- [ ] **Record pricing/cost audios** adapted to industry standards
- [ ] **Record objection handling audios** for common industry concerns
- [ ] **Record demo/closing audios** with industry-specific language

**File Naming Convention:**
```
OLD (Schools): intro_klariqo.mp3
NEW (Hotels): intro_klariqo_hotels.mp3

OLD: agents_need_no_breaks.mp3 (about school reception)
NEW: reception_staff_24_7.mp3 (about hotel reception)

OLD: klariqo_pricing.mp3 (school pricing)
NEW: hotel_pricing_structure.mp3 (hotel pricing)
```

#### 2.2 Audio File Management
**Required Actions:**
- [ ] **Create new MP3 files** in `audio/` folder
- [ ] **Update Excel file** `audio_files.xlsx` with new entries
- [ ] **Run conversion script**: `python excel_to_json.py`
- [ ] **Convert to PCM format**: `python audio-optimiser.py`
- [ ] **Test audio loading**: Verify files in `audio_pcm/` folder

---

### **PHASE 3: CONVERSATION LOGIC ADAPTATION**

#### 3.1 Update Router Prompt
**Files to modify:** `router.py`, `router_gemini.py`

**Required Changes:**
```python
# OLD (Line 27):
prompt = f"""You are Nisha's audio file selector for Klariqo sales calls targeting school principals."""

# NEW (Hotels example):
prompt = f"""You are Nisha's audio file selector for Klariqo sales calls targeting hotel managers/owners."""

# OLD (Line 41):
User shows interest → klariqo_provides_voice_agent1.mp3 + voice_agents_trained_details.mp3

# NEW (Hotels example):  
User shows interest → hotel_voice_agent_intro.mp3 + guest_service_automation.mp3
```

#### 3.2 Update Matching Rules
**Required Actions:**
- [ ] **Replace all school-specific rules** with industry-specific ones
- [ ] **Update file references** to new audio files
- [ ] **Add industry-specific objections** and responses
- [ ] **Modify pricing conversation flow** for the new industry

**Example Rule Updates for Hotels:**
```python
# OLD (Schools):
User asks how this helps if they already have receptionist/team → agents_need_no_breaks.mp3

# NEW (Hotels):
User asks about replacing reception staff → reception_24_7_benefits.mp3 + multilingual_support.mp3

# OLD (Schools):
User asks pricing/cost/fees → klariqo_pricing.mp3 + 3000_mins_breakdown.mp3

# NEW (Hotels):
User asks pricing/cost/fees → hotel_pricing_structure.mp3 + guest_inquiry_volume.mp3
```

---

### **PHASE 4: CONFIGURATION UPDATES**

#### 4.1 Update Session Flags
**File:** `config.py` (Lines 50-58)

**Required Changes:**
```python
# OLD (Schools):
SESSION_FLAGS_TEMPLATE = {
    "intro_played": False,
    "klariqo_explained": False, 
    "features_discussed": False,
    "pricing_mentioned": False,
    "demo_offered": False,
    "meeting_scheduled": False
}

# NEW (Hotels example):
SESSION_FLAGS_TEMPLATE = {
    "intro_played": False,
    "hotel_benefits_explained": False,
    "guest_service_features_discussed": False,
    "pricing_mentioned": False,
    "demo_offered": False,
    "meeting_scheduled": False,
    "multilingual_discussed": False,  # Industry-specific flag
    "peak_season_concerns_addressed": False  # Industry-specific flag
}
```

#### 4.2 Update Voice Character (Optional)
**File:** `config.py` (Line 27)

**Consider changing:**
```python
# Current:
VOICE_ID = "TRnaQb7q41oL7sV0w6Bu"  # Nisha's voice

# Options:
# - Keep same voice for consistency
# - Change to more professional voice for B2B industries
# - Change to warmer voice for hospitality industries
```

---

### **PHASE 5: AUDIO SNIPPETS CONFIGURATION**

#### 5.1 Update JSON Structure
**File:** `audio_snippets.json`

**Required Actions:**
- [ ] **Replace all file references** with new industry-specific files
- [ ] **Update transcripts** to match new audio content
- [ ] **Reorganize categories** to match new industry flow
- [ ] **Add new categories** specific to the industry

**Example Structure for Hotels:**
```json
{
  "introductions": {
    "intro_klariqo_hotels.mp3": "[confident] Hi! I'm Nisha from Klariqo, and I need just 2 minutes to show you how hotels like yours are handling 3x more guest inquiries automatically..."
  },
  "guest_service_features": {
    "reception_24_7_benefits.mp3": "Our voice agents work 24/7, handling guest inquiries even during night shifts, peak check-in times, and holidays...",
    "multilingual_support.mp3": "The agent can communicate in multiple languages for your international guests...",
    "room_availability_handling.mp3": "It can instantly check room availability and guide guests through booking..."
  },
  "hotel_operations": {
    "concierge_services.mp3": "The agent can provide local recommendations, restaurant suggestions, and area information...",
    "complaint_handling.mp3": "For complaints or issues, it can escalate to the right staff member..."
  },
  "pricing_hotels": {
    "hotel_pricing_structure.mp3": "For hotels, our pricing is designed to be much more cost-effective than hiring additional reception staff...",
    "guest_inquiry_volume.mp3": "Based on average hotel inquiry patterns, you can handle 200+ guest calls per day..."
  }
}
```

---

### **PHASE 6: TESTING & VALIDATION**

#### 6.1 System Testing
**Required Actions:**
- [ ] **Test audio file loading**: `python -c "from audio_manager import audio_manager; print(f'Loaded: {len(audio_manager.memory_cache)} files')"`
- [ ] **Test conversation flow**: Use `/test` endpoint to simulate conversations
- [ ] **Verify router responses**: Check that new rules are working
- [ ] **Test session flags**: Ensure industry-specific tracking works

#### 6.2 Content Quality Check
**Required Actions:**
- [ ] **Audio quality verification**: All PCM files play correctly
- [ ] **Transcript accuracy**: JSON transcripts match audio content
- [ ] **Conversation flow logic**: Natural progression through industry scenarios
- [ ] **Fallback responses**: TTS generates appropriate content for edge cases

---

### **PHASE 7: DEPLOYMENT PREPARATION**

#### 7.1 Environment Configuration
**File:** `.env`

**Consider updating:**
```env
# Voice settings for new industry
VOICE_ID=new_voice_id_for_industry  # If changing voice

# Update any industry-specific API keys or settings
INDUSTRY_SPECIFIC_API_KEY=your_key  # If needed
```

#### 7.2 Documentation Updates
**Required Actions:**
- [ ] **Update README.md** with new industry context
- [ ] **Update system description** in health check endpoint (`main.py` line 67)
- [ ] **Update file structure documentation** if needed
- [ ] **Create industry-specific testing guide**

---

## 🏭 INDUSTRY-SPECIFIC EXAMPLES

### **Hotels/Hospitality Example:**
```
Target: Hotel managers, boutique hotel owners
Agent Name: Nisha (Hotel Guest Service Specialist)
Value Prop: "Handle 3x more guest inquiries with 24/7 multilingual support"
Key Features: Room availability, booking assistance, concierge services, complaint escalation
Pricing: Based on guest inquiry volume rather than admissions volume
```

### **Hospitals/Healthcare Example:**
```
Target: Hospital administrators, clinic managers  
Agent Name: Nisha (Healthcare Assistant)
Value Prop: "Streamline patient inquiries and appointment scheduling 24/7"
Key Features: Appointment booking, department information, visiting hours, emergency protocols
Pricing: Based on patient inquiry volume and appointment bookings
```

### **Restaurants Example:**
```
Target: Restaurant owners, chain managers
Agent Name: Nisha (Restaurant Host)
Value Prop: "Never miss a reservation with 24/7 automated booking assistant"
Key Features: Table reservations, menu inquiries, special dietary requirements, event bookings
Pricing: Based on reservation volume and customer inquiries
```

### **Real Estate Example:**
```
Target: Real estate agencies, property managers
Agent Name: Nisha (Property Specialist)  
Value Prop: "Qualify leads and schedule viewings while you focus on closing deals"
Key Features: Property information, viewing scheduling, pricing details, location benefits
Pricing: Based on lead volume and viewing appointments scheduled
```

---

## ⚠️ COMMON PITFALLS TO AVOID

### **Technical Issues:**
- [ ] **File naming conflicts**: Don't overwrite existing files, create new ones
- [ ] **PCM conversion**: Always run `audio-optimiser.py` after adding new MP3 files
- [ ] **JSON syntax**: Validate `audio_snippets.json` for proper JSON format
- [ ] **Router testing**: Test all conversation paths before deployment

### **Content Issues:**
- [ ] **Industry research**: Don't assume pain points, research the specific industry
- [ ] **Terminology accuracy**: Use correct industry terms and acronyms
- [ ] **Cultural sensitivity**: Consider cultural aspects of the target industry
- [ ] **Compliance**: Check if industry has specific communication regulations

### **Business Logic Issues:**
- [ ] **Pricing alignment**: Ensure pricing makes sense for industry economics
- [ ] **Value proposition**: Clear differentiation from existing industry solutions
- [ ] **Feature relevance**: Only include features that matter to the industry
- [ ] **Demo approach**: Tailor demo to industry-specific scenarios

---

## 🚀 QUICK START CHECKLIST

### **For a New Industry Adaptation:**

**Week 1: Planning & Research**
- [ ] Research target industry pain points and terminology
- [ ] Create conversation flow map for new industry
- [ ] Write scripts for all conversation scenarios
- [ ] Plan audio file structure and naming

**Week 2: Content Creation**
- [ ] Record new industry-specific audio files
- [ ] Update `audio_files.xlsx` with new entries
- [ ] Convert Excel to JSON and MP3 to PCM
- [ ] Test audio file loading and playback

**Week 3: System Configuration**  
- [ ] Update router prompts and matching rules
- [ ] Modify session flags and configuration
- [ ] Update `audio_snippets.json` structure
- [ ] Configure any industry-specific settings

**Week 4: Testing & Deployment**
- [ ] Comprehensive conversation flow testing
- [ ] Audio quality and routing verification
- [ ] Performance testing under load
- [ ] Documentation updates and deployment

---

## 📞 SUPPORT & TROUBLESHOOTING

### **Common Issues During Adaptation:**

**"New audio files not loading"**
- ✅ Check files exist in both `audio/` and `audio_pcm/` folders
- ✅ Verify Excel to JSON conversion completed successfully
- ✅ Restart the system to reload audio cache

**"Router not selecting new files"**
- ✅ Check router prompt references correct file names
- ✅ Verify matching rules use exact file names from JSON
- ✅ Test individual rules with debug endpoints

**"Conversation flow feels unnatural"**
- ✅ Review industry research for appropriate terminology  
- ✅ Test conversation with industry stakeholders
- ✅ Adjust chaining of audio files for better flow

**"System performance issues"**
- ✅ Monitor memory usage with many new audio files
- ✅ Check PCM file sizes and compression
- ✅ Verify proper chunking for telephony systems

---

## 📝 FINAL NOTES

This adaptation process typically takes **2-4 weeks** depending on:
- **Industry complexity** (healthcare vs. restaurants)
- **Content volume** (number of scenarios to cover)
- **Audio quality requirements** (voice acting vs. simple recording)
- **Integration complexity** (new APIs, compliance requirements)

**Success Metrics:**
- Conversation completion rate > 80%
- Natural conversation flow (user feedback)
- Appropriate industry terminology usage
- Effective handling of industry-specific objections
- Meeting booking/conversion rates

**For technical support during adaptation, use:**
- Debug endpoints: `/debug/system_health`, `/test`
- Log analysis: `logs/call_logs.csv`, `logs/conversation_logs.csv`
- Audio validation: Memory cache stats and file loading tests

---

*Built with ❤️ by the Klariqo Team - Adaptable for any industry*