# 🔄 CLIENT ADAPTATION GUIDE
## Complete Guide for Freelancers & VAs to Adapt This System for New Clients

---

### 🎯 **Overview: What This Guide Covers**

This guide helps freelancers/VAs clone and adapt the Klariqo AI Voice Assistant for **new clients** across different industries:
- 🏫 **Schools** → 🏨 **Hotels** → 🏥 **Hospitals** → 🏢 **Offices** → 🛒 **E-commerce**

**Time Required:** 4-6 hours for complete adaptation  
**Skills Needed:** Basic Git, Excel, Audio editing  
**Result:** Fully customized AI voice system for new client

---

## 📋 **PHASE 1: Repository Setup (30 minutes)**

### **Step 1: Create New Repository for Client**
```bash
# 1. Clone the original as a NEW repository (don't fork!)
git clone https://github.com/original/klariqo-schools.git
cd klariqo-schools

# 2. Remove original git history (create fresh repo)
rm -rf .git
git init
git add .
git commit -m "Initial commit: AI Voice Assistant for [CLIENT_NAME]"

# 3. Create new GitHub repository and push
# Go to GitHub.com → Create New Repository → "client-name-voice-ai"
git remote add origin https://github.com/your-username/CLIENT-NAME-voice-ai.git
git branch -M main
git push -u origin main
```

### **Step 2: Rename Project Files**
```bash
# Update project name throughout codebase
# Find & Replace in ALL files:
# "AVS International School" → "[CLIENT BUSINESS NAME]"
# "Nisha" → "[CLIENT PREFERRED AI NAME]"
# "school" → "[CLIENT INDUSTRY]"
# "parent" → "[CLIENT TARGET AUDIENCE]"

# Key files to update:
# - README.md (title, descriptions)
# - main.py (header comments, health check)
# - config.py (SESSION_FLAGS_TEMPLATE, SESSION_VARIABLES_TEMPLATE)
# - router.py (prompts, user types)
# - audio_snippets.json (all transcripts)
```

---

## 🎵 **PHASE 2: Audio Content Adaptation (3-4 hours)**

### **Step 1: Industry Analysis & Content Planning**

**For Hotels:**
```bash
# Common inquiries to cover:
# - Room availability & rates
# - Check-in/check-out times  
# - Amenities (pool, gym, restaurant)
# - Location & directions
# - Booking modifications
# - Special services (spa, room service)
# - Event hosting capabilities

# Session variables to track:
# - check_in_date, check_out_date
# - room_type, guest_count
# - special_requests, budget_range
```

**For Hospitals:**
```bash
# Common inquiries to cover:
# - Doctor availability & appointments
# - Department information
# - Visiting hours & policies
# - Insurance & billing
# - Emergency procedures
# - Test results inquiry
# - Patient room information

# Session variables to track:
# - patient_name, doctor_preference
# - department_needed, urgency_level
# - insurance_type, appointment_date
```

**For E-commerce:**
```bash
# Common inquiries to cover:
# - Order status & tracking
# - Return/exchange policy
# - Product availability
# - Payment & shipping options
# - Account issues
# - Promotional offers
# - Technical support

# Session variables to track:
# - order_number, product_interest
# - customer_type, issue_category
# - payment_method, shipping_address
```

### **Step 2: Create New Audio Content**

#### **Update Excel Management File**
```bash
# 1. Open audio_files.xlsx
# 2. Replace ALL content with new industry-specific responses
# 3. Structure by categories relevant to client:

# Example for Hotel:
Category | Filename | Transcript | Alternate_Version
---------|----------|------------|------------------
introductions | hotel_intro.mp3 | "Welcome to [HOTEL NAME]..." | hotel_intro_2.mp3
room_inquiries | room_availability.mp3 | "Let me check our availability..." | ""
amenities | amenities_overview.mp3 | "Our hotel features..." | ""
booking | booking_process.mp3 | "To make a reservation..." | ""
```

#### **Record New Audio Files**
```bash
# 1. Script writing (use same speaking style as original)
#    - Keep same tone: professional, helpful, conversational
#    - Mix languages if applicable (Hindi+English for Indian clients)
#    - Use client-specific terminology

# 2. Recording requirements:
#    - Same voice actor (consistency)
#    - Same recording quality (clear, no background noise)
#    - Same format: MP3, good quality
#    - Length: 15-60 seconds per response

# 3. File naming convention:
#    - industry_topic.mp3 (e.g., hotel_checkout.mp3)
#    - Keep filenames descriptive but concise
#    - No spaces, use underscores
```

### **Step 3: Audio File Processing**
```bash
# 1. Place new MP3 files in audio/ directory
# 2. Update Excel file with all new content
# 3. Convert Excel to JSON:
python excel_to_json.py
# Select option 1 to convert

# 4. Convert MP3 to PCM format:
python audio-optimiser.py
# This creates audio_pcm/ directory with telephony-ready files

# 5. Verify conversion:
ls audio_pcm/  # Should show all your new .pcm files
```

---

## ⚙️ **PHASE 3: Configuration Updates (1 hour)**

### **Step 1: Update Session Management**
```python
# In config.py, update SESSION_FLAGS_TEMPLATE:

# For Hotel:
SESSION_FLAGS_TEMPLATE = {
    "intro_played": False,
    "room_inquiry_made": False,
    "amenities_discussed": False,
    "rates_mentioned": False,
    "booking_attempted": False,
    "location_discussed": False,
    "special_services_mentioned": False
}

SESSION_VARIABLES_TEMPLATE = {
    "check_in_date": None,
    "check_out_date": None,
    "room_type": None,
    "guest_count": None,
    "budget_range": None,
    "special_requests": None,
    "customer_name": None,
    "inquiry_focus": None  # "rooms", "dining", "events", etc.
}
```

### **Step 2: Update AI Response Logic**
```python
# In router.py, update the base prompt:

# Replace school-specific prompts with industry-specific ones
# Update file selection rules
# Modify context understanding for new industry

# Example for hotel:
prompt = f"""You are [AI_NAME], a helpful voice assistant at [HOTEL_NAME]. 
Your job is to respond to guest inquiries with appropriate audio responses.

🏨 HOTEL RESPONSE RULES:
Guest asks about rooms → If dates known: room_availability.mp3
Guest mentions dates → room_rates_[SEASON].mp3  
Guest asks amenities → amenities_overview.mp3
Guest wants to book → booking_process.mp3
..."""
```

### **Step 3: Update Voice & TTS Settings**
```python
# In config.py, update voice settings:
VOICE_ID = "NEW_VOICE_ID"  # ElevenLabs voice for client
DEEPGRAM_LANGUAGE = "en"   # Adjust language if needed

# In tts_engine.py, adjust voice settings for industry:
voice_settings = VoiceSettings(
    stability=0.6,           # Higher for professional industries
    similarity_boost=0.8,
    style=0.1,              # Slight style for hospitality
    use_speaker_boost=True   # For clearer phone audio
)
```

---

## 🧪 **PHASE 4: Testing & Validation (1 hour)**

### **Step 1: Audio Testing**
```bash
# 1. Test audio file loading:
python main.py
# Should see: "🎵 PCM cache: [N] files loaded"

# 2. Test individual audio files:
# Use /test endpoint to play specific files
# Verify all audio is clear and appropriate

# 3. Test audio chains:
# Ensure multiple files can play together smoothly
```

### **Step 2: Conversation Flow Testing**
```bash
# Create test scenarios for new industry:

# Hotel Test Scenarios:
# 1. "I want to book a room for this weekend"
# 2. "What amenities do you have?"  
# 3. "Can you tell me your rates?"
# 4. "I need to modify my reservation"

# Expected AI responses:
# - Should ask for dates if not provided
# - Should mention specific amenities
# - Should provide rate information
# - Should guide to booking process
```

### **Step 3: Session Memory Testing**
```bash
# Test that session variables are tracked correctly:
# 1. Mention dates → system should remember
# 2. Ask about rooms → should use remembered dates
# 3. Verify no repetitive responses
# 4. Check conversation history logging
```

---

## 🚀 **PHASE 5: Client Delivery (30 minutes)**

### **Step 1: Documentation Update**
```bash
# 1. Update README.md:
#    - Change title to client business
#    - Update industry-specific examples
#    - Modify deployment instructions for client context

# 2. Create CLIENT_SETUP.md:
#    - Client-specific API keys needed
#    - Exotel/Twilio number configuration
#    - Business-specific webhook URLs
#    - Go-live checklist
```

### **Step 2: Environment Configuration**
```bash
# 1. Create client-specific .env.example:
# Copy your .env but replace actual keys with placeholders
cp .env .env.example
# Edit .env.example to remove real API keys

# 2. Document API accounts needed:
#    - Deepgram (same for all)
#    - OpenAI/Gemini (same for all)  
#    - ElevenLabs (may need new voice)
#    - Exotel/Twilio (client's account)
```

### **Step 3: Deployment Package**
```bash
# Create deployment package for client:
# 1. Clean repository (remove logs, temp files)
# 2. Test fresh clone and setup
# 3. Create deployment checklist
# 4. Record demonstration video

# Final deliverables:
# ✅ GitHub repository with new client code
# ✅ All audio files (MP3 + PCM)
# ✅ Updated configuration
# ✅ Testing documentation
# ✅ Deployment guide
# ✅ Demo video
```

---

## 📊 **Industry-Specific Quick Guides**

### **🏨 Hotel Adaptation Checklist**
- [ ] Room types & availability responses
- [ ] Amenities & services overview
- [ ] Booking & reservation process
- [ ] Rate information by season
- [ ] Location & directions
- [ ] Special services (spa, dining, events)
- [ ] Guest services & concierge

### **🏥 Hospital Adaptation Checklist**  
- [ ] Department & doctor information
- [ ] Appointment scheduling process
- [ ] Visiting hours & policies
- [ ] Insurance & billing guidance
- [ ] Emergency procedures
- [ ] Test results & reports
- [ ] Patient care services

### **🛒 E-commerce Adaptation Checklist**
- [ ] Order status & tracking
- [ ] Product information & availability  
- [ ] Return & exchange policies
- [ ] Payment & shipping options
- [ ] Account & login assistance
- [ ] Promotional offers
- [ ] Technical support

---

## ⚠️ **Common Pitfalls & Solutions**

### **Audio File Issues**
```bash
# Problem: PCM conversion fails
# Solution: Check MP3 file quality, ensure no silence at start/end

# Problem: Audio sounds robotic
# Solution: Record with more natural pauses, use professional voice actor

# Problem: Files too large for git
# Solution: Use deployment options in main README, keep audio separate
```

### **Configuration Issues**
```bash
# Problem: AI gives wrong responses
# Solution: Update prompts with industry-specific examples

# Problem: Session variables not tracking
# Solution: Verify variable names match in config.py and router.py

# Problem: TTS fallback not working
# Solution: Check ElevenLabs API key and voice ID for new voice
```

### **Deployment Issues**
```bash
# Problem: Audio files missing on production
# Solution: Use audio deployment options from main README

# Problem: Environment variables not loading
# Solution: Verify .env file is copied to production server

# Problem: Exotel integration fails
# Solution: Check webhook URLs match client's domain
```

---

## 💰 **Pricing Guide for Clients**

### **Development Cost Breakdown**
- **Repository Setup:** $200-400
- **Audio Content Creation:** $800-1,500 (depends on # of responses)
- **Configuration & Testing:** $400-600
- **Deployment & Training:** $300-500
- **Total Project:** $1,700-3,000

### **Ongoing Costs (Monthly)**
- **Server Hosting:** $50-100
- **Exotel/Twilio:** $100-300 (based on call volume)
- **API Costs:** $50-150 (Deepgram, OpenAI, ElevenLabs)
- **Maintenance:** $200-400
- **Total Monthly:** $400-950

---

## 📞 **Support & Next Steps**

### **For Freelancers/VAs:**
1. **Follow this guide step-by-step**
2. **Test thoroughly before client delivery**
3. **Keep original repository as template for future clients**
4. **Document any client-specific customizations**

### **For Clients:**
1. **Review adapted system thoroughly**
2. **Test with real business scenarios**
3. **Provide feedback for improvements**
4. **Schedule training for staff**

### **Quality Assurance Checklist:**
- [ ] All audio files play correctly
- [ ] Session memory works as expected
- [ ] Industry-specific responses are accurate
- [ ] No references to original school remain
- [ ] Configuration matches client business
- [ ] Deployment documentation is complete

---

**🎉 Congratulations!** You've successfully adapted the Klariqo AI Voice Assistant for a new client. The system is now ready for production deployment in their specific industry.

**Next:** Follow the deployment guide in the main README.md to go live!