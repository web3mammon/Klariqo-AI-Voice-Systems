# 🚀 Klariqo School System v2.5

**AI-Powered Voice Sales Agent for Schools** | Ultra-Fast PCM Streaming | Patent-Pending Technology

Klariqo uses our revolutionary **Modular Voice Response System** to create the most human-sounding AI voice agents that sell your product while you sleep. This implementation specifically targets school principals to pitch Klariqo's voice AI services.

## 🆕 **Version 2.5 - Major Performance Updates**

### **🎵 PCM Audio Revolution**
- **Direct PCM Streaming** - No conversion overhead, direct audio serving
- **Exotel Integration** - Full bidirectional streaming with proper chunking
- **Memory-Cached PCM** - All audio files loaded into RAM for instant access
- **Excel-to-JSON Converter** - Manage all audio files via simple Excel spreadsheet
- **Hybrid Audio System** - Pre-recorded snippets + TTS fallback with PCM conversion

### **⚡ Performance Optimizations**
- **0-50ms Response Time** - Pre-recorded snippets served directly from memory
- **PCM Format Compliance** - 16-bit, 8kHz, mono PCM for telephony systems
- **Proper Chunking** - 3200-byte chunks for optimal streaming
- **TTS Fallback** - Dynamic MP3→PCM conversion when snippets unavailable

### **🤖 Enhanced AI Engine**
- **Multi-Model Support** - Switch between Groq (Llama), OpenAI (GPT-3.5/4), or Gemini
- **Smart File Selection** - AI automatically chooses appropriate audio responses
- **Structured Prompting** - Rule-based responses with intelligent fallbacks
- **Session Memory** - Prevents repetitive responses, natural conversations

### **📊 Enterprise Features** 
- **Comprehensive Logging** - Every call tracked in CSV format
- **Session Management** - Handles concurrent calls with isolated state
- **Hot Reloading** - Update audio library without system restart
- **Debug Endpoints** - System health monitoring and troubleshooting

## 🎯 What This Does

- **Nisha** (our AI agent) calls school principals to pitch Klariqo
- Handles both **inbound** (demo calls) and **outbound** (cold calls) 
- Uses **pre-recorded PCM audio snippets** for ultra-fast, human-like responses
- **Smart AI selection** matches user input to appropriate audio responses
- Falls back to **real-time TTS** (with PCM conversion) only when needed
- **Excel-driven content management** for easy updates by non-technical team
- Logs every conversation for analysis and improvement
- **Multi-telephony support** (Twilio + Exotel)

## 🔄 Adapting to New Industries

**Want to use this system for hotels, hospitals, restaurants, or any other industry?**

📖 **See [CLIENT_ADAPTATION_GUIDE.md](CLIENT_ADAPTATION_GUIDE.md)** for complete step-by-step instructions to adapt this system from schools to any new industry.

The guide covers:
- ✅ **Content planning** for new industries (hotels, hospitals, etc.)
- ✅ **Audio file creation** and management workflows  
- ✅ **Conversation logic** updates for different audiences
- ✅ **System configuration** changes required
- ✅ **Testing and validation** procedures
- ✅ **Industry-specific examples** with sample scripts

## 🏗️ Architecture

```
├── main.py                 # Application runner & WebSocket handler with PCM streaming
├── config.py              # Centralized configuration management  
├── session.py             # Call session state management
├── router.py              # AI-powered response selection (Multi-model support)
├── audio_manager.py       # PCM audio file library management with memory caching
├── tts_engine.py          # ElevenLabs TTS fallback with MP3→PCM conversion
├── logger.py              # Structured call logging to CSV
├── routes/
│   ├── inbound.py         # Inbound call handlers
│   ├── outbound.py        # Outbound call & campaign management
│   ├── exotel.py          # Exotel integration routes
│   └── test.py            # Testing & debug endpoints
├── audio/                 # Original high-quality audio files (MP3)
├── audio_pcm/             # PCM audio files (16-bit, 8kHz, mono) - USED BY SYSTEM
├── logs/                  # Call logs and conversation transcripts
├── temp/                  # Temporary TTS generated files
├── audio_snippets.json    # Auto-generated from Excel (don't edit manually)
├── audio_files.xlsx       # YOUR MAIN AUDIO MANAGEMENT FILE
├── excel_to_json.py       # Excel to JSON converter script
├── audio-optimiser.py     # MP3→PCM conversion utility
├── .env                   # Environment variables & API keys
└── requirements.txt       # Python dependencies
```

## 📋 Prerequisites

1. **Python 3.8+** 
2. **API Accounts:**
   - [Twilio](https://twilio.com) or [Exotel](https://exotel.com) - Voice calling & streaming
   - [Deepgram](https://deepgram.com) - Speech-to-Text
   - [OpenAI](https://openai.com) or [Groq](https://groq.com) - LLM for response selection
   - [ElevenLabs](https://elevenlabs.io) - Text-to-Speech fallback
3. **ngrok** - For local development webhooks
4. **Audio Libraries** - `librosa` and `numpy` for TTS PCM conversion

## 🚀 Quick Setup

### 1. Clone & Install
```bash
git clone <your-repo>
cd klariqo-school-system
pip install -r requirements.txt

# Install audio processing libraries for TTS fallback
pip install librosa numpy
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
nano .env
```

Required variables:
```env
# Speech & AI Services
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# AI Model Selection (choose one or multiple)
OPENAI_API_KEY=your_openai_key            # Reliable GPT-3.5/4 (200-500ms)
GROQ_API_KEY=your_groq_key                # Ultra-fast Llama (50-100ms)
GEMINI_API_KEY=your_gemini_key            # Google's Gemini model

# Telephony Services (choose one)
TWILIO_ACCOUNT_SID=your_twilio_sid        # For Twilio
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE=+1234567890

# OR use Exotel (recommended for Indian market)
EXOTEL_ACCOUNT_SID=your_exotel_sid
EXOTEL_API_TOKEN=your_exotel_token
```

### 3. Prepare Audio Files & PCM Conversion

**CRITICAL: Audio files must be in PCM format for telephony systems**

```bash
# 1. Create your audio management Excel file
# Columns: Filename | Transcript | Category | Alternate_Version

# 2. Convert Excel to JSON
python excel_to_json.py
# Choose option 1 to convert

# 3. Convert MP3 files to PCM format (REQUIRED)
python audio-optimiser.py
# This converts audio/ → audio_pcm/ (PCM format)

# 4. Your directory structure:
mkdir audio                    # Original MP3 files from recording
mkdir audio_pcm               # PCM files (system uses these)
mkdir temp                    # Temporary TTS files
mkdir logs                    # Call logs and analytics
```

**Excel Structure Example:**
| Filename | Transcript | Category | Alternate_Version |
|----------|------------|----------|-------------------|
| intro_klariqo.mp3 | नमस्ते! मैं निशा... | introductions | intro_klariqo2.mp3 |
| pricing_basic.mp3 | हमारी pricing... | pricing | pricing_detailed.mp3 |

### 4. Run the System
```bash
python main.py
```

The system will:
- ✅ Validate configuration and API keys
- 🎵 Load PCM audio files into memory cache
- 🌐 Start ngrok tunnel (for webhooks)
- 📞 Display webhook URLs for Twilio/Exotel
- 🧪 Provide test page URL

## 🎵 PCM Audio System (NEW!)

### **Understanding the Audio Flow**

**For New Developers:** Our system uses a hybrid approach for optimal performance:

1. **Pre-recorded Responses (95% of calls)**: 
   - AI selects appropriate audio file
   - System serves PCM data directly from memory
   - **Latency: 0-50ms** ⚡

2. **TTS Fallback (5% of calls)**:
   - AI generates text response
   - ElevenLabs creates MP3 audio
   - System converts MP3→PCM in real-time
   - **Latency: 200-500ms** 🔄

### **Excel-Based Workflow (For Content Teams)**

**Step 1: Create/Update Audio Content**
```bash
# 1. Record new audio as MP3 files
# 2. Save to audio/ folder
# 3. Update audio_files.xlsx with new entries
# 4. Run converter: python excel_to_json.py
# 5. Convert to PCM: python audio-optimiser.py
# 6. Restart system: python main.py
```

**Step 2: Excel File Structure**
- **Filename**: `intro_klariqo.mp3` (without path)
- **Transcript**: `नमस्ते! मैं निशा बोल रही हूं...` (what Nisha says)
- **Category**: `introductions` (auto-categorization)
- **Alternate_Version**: `intro_klariqo2.mp3` (optional variation)

### **PCM Technical Details (For Developers)**

**Why PCM Format?**
- **Telephony Standard**: All phone systems use PCM
- **No Conversion Overhead**: Direct streaming to callers
- **Exotel Compliance**: 16-bit, 8kHz, mono PCM required
- **Chunking**: 3200-byte chunks for optimal streaming

**Audio Manager Implementation:**
```python
# System loads PCM files but stores with MP3 keys for compatibility
audio_manager.memory_cache["intro_klariqo.mp3"] = pcm_bytes_data

# AI router uses MP3 references
router_response = "intro_klariqo.mp3 + pricing_basic.mp3"

# System fetches PCM data and streams to caller
```

## 🧪 Testing

### Browser Testing
1. Go to `http://your-ngrok-url/test`
2. Click "Call +919876543210" (update with your number)
3. Answer the call and pretend to be a school principal
4. Experience Nisha pitching Klariqo with ultra-low latency!

### API Testing
```bash
# Start outbound campaign
curl -X POST http://your-ngrok-url/outbound/start_campaign

# Check system health with PCM cache status
curl http://your-ngrok-url/debug/system_health

# Exotel integration test
curl http://your-ngrok-url/exotel/debug
```

## 📞 Telephony Integration

### **Exotel Setup (Recommended for India)**
```bash
# Configure in Exotel Dashboard:
# 1. Incoming Call URL: https://your-domain.com/exotel/voice
# 2. Voicebot URL: https://your-domain.com/exotel/get_websocket
# 3. Enable bidirectional streaming
# 4. Set audio format: PCM, 16-bit, 8kHz, mono
```

### **Twilio Setup (Global)**
```bash
# Configure in Twilio Console:
# 1. Webhook URL: https://your-domain.com/twilio/voice
# 2. HTTP Method: POST
# 3. Enable WebSocket streaming
```

## 🤖 AI Model Configuration

### **Switching AI Models (For Developers)**

**Current Default: OpenAI GPT-3.5-turbo**
```python
# In router.py
from openai import OpenAI
client = OpenAI(api_key=Config.OPENAI_API_KEY)
model = "gpt-3.5-turbo"  # Reliable, 200-500ms
```

**Ultra-Fast Option: Groq Llama**
```python
# In router.py
from groq import Groq
client = Groq(api_key=Config.GROQ_API_KEY)
model = "llama-3.1-8b-instant"  # 50-100ms
```

**Google Option: Gemini**
```python
# In router_gemini.py (alternative router)
import google.generativeai as genai
genai.configure(api_key=Config.GEMINI_API_KEY)
model = "gemini-1.5-flash"  # Fast and reliable
```

### **Model Performance Comparison**
| Model | Speed | Reliability | Cost/1M tokens | Best For |
|-------|-------|-------------|----------------|----------|
| Llama-3.1-8b | 🚀 50-100ms | ⭐⭐⭐ | $0.10 | Speed-critical calls |
| GPT-3.5-turbo | ⚡ 200-500ms | ⭐⭐⭐⭐⭐ | $0.50 | Production reliability |
| Gemini-1.5-flash | ⚡ 150-300ms | ⭐⭐⭐⭐ | $0.15 | Cost-effective option |

## 🔧 Advanced Configuration

### **For Content Teams (Non-Technical)**

**Adding New Responses:**
1. Record new MP3 file and save to `audio/` folder
2. Open `audio_files.xlsx` in Excel
3. Add new row with filename and transcript
4. Run: `python excel_to_json.py` (choose option 1)
5. Run: `python audio-optimiser.py` (converts to PCM)
6. Restart system: `python main.py`

**Updating Existing Content:**
1. Replace MP3 file in `audio/` folder
2. Update transcript in Excel if needed
3. Re-run converter and optimizer
4. System will auto-reload new content

### **For Developers**

**Custom Response Logic:**
```python
# In router.py, add new matching rules:
User asks about scholarships → scholarship_info.mp3 + eligibility_criteria.mp3
```

**Session Memory Flags:**
```python
# In config.py, add new tracking flags:
SESSION_FLAGS_TEMPLATE = {
    "intro_played": False,
    "pricing_mentioned": False,
    "scholarship_discussed": False,  # New flag
}
```

**PCM Audio Validation:**
```python
# Test PCM cache loading
python -c "from audio_manager import audio_manager; print(f'Loaded: {len(audio_manager.memory_cache)} files')"
```

## 🐛 Troubleshooting

### **Common Issues for New Team Members**

**"No audio files found in cache"**
- ✅ Check `audio_pcm/` folder exists and has `.pcm` files
- ✅ Run `python excel_to_json.py` to update JSON
- ✅ Run `python audio-optimiser.py` to convert MP3→PCM
- ✅ Verify filenames in Excel match actual files

**"PCM audio file not in cache"**
- ✅ Check `audio_snippets.json` uses `.mp3` extensions (not `.pcm`)
- ✅ Ensure PCM files exist in `audio_pcm/` folder
- ✅ Restart system to reload audio cache

**"TTS MP3 to PCM conversion failed"**
- ✅ Install missing libraries: `pip install librosa numpy`
- ✅ Check ElevenLabs API quota and voice ID
- ✅ Test TTS separately: `python -c "from tts_engine import tts_engine; print(tts_engine.generate_audio('test'))"`

**"Exotel audio choppy or distorted"**
- ✅ Verify PCM format: 16-bit, 8kHz, mono
- ✅ Check chunk size is 3200 bytes
- ✅ Test with single audio file first

### **Debug Commands**
```bash
# Test audio cache loading
python -c "from audio_manager import audio_manager; print(f'Cache: {len(audio_manager.memory_cache)} files')"

# Test specific file
python -c "from audio_manager import audio_manager; print('intro_klariqo.mp3' in audio_manager.memory_cache)"

# View memory usage
python -c "from audio_manager import audio_manager; stats = audio_manager.get_memory_stats(); print(f'Total: {stats[\"total_size_mb\"]:.1f}MB')"

# Test TTS conversion
python -c "from main import convert_mp3_to_pcm_for_tts; print('TTS conversion available:', convert_mp3_to_pcm_for_tts is not None)"

# View logs
tail -f logs/call_logs.csv
tail -f logs/conversation_logs.csv
```

## 📈 Performance Metrics & Updates

### **Version 2.5 Benchmarks (Current)**
- **Pre-recorded Audio Response**: 0-50ms (PCM direct from memory)
- **TTS Fallback Response**: 200-500ms (MP3→PCM conversion)
- **Memory Usage**: ~15-25MB for 35 PCM audio files
- **File Loading**: Instant (all files pre-cached in RAM)
- **Telephony Compatibility**: 100% (proper PCM format)
- **AI Accuracy**: 95%+ with structured prompting

### **Performance Comparison**
| Metric | v2.0 (MP3) | v2.5 (PCM) | Improvement |
|--------|-------------|-------------|-------------|
| Response Time | 200-700ms | 0-50ms | 🚀 14x faster |
| Memory Usage | 3.6MB | 15MB | More memory, instant access |
| Audio Quality | Compressed | Telephony-optimized | Superior clarity |
| Conversion Overhead | Every call | None (pre-converted) | Zero overhead |

### **Recent Major Updates**

**v2.5 (Current) - PCM Revolution**
- ✅ Direct PCM audio streaming (0-50ms responses)
- ✅ Exotel bidirectional streaming integration
- ✅ Memory-cached audio files for instant access
- ✅ TTS fallback with real-time MP3→PCM conversion
- ✅ Proper audio chunking for telephony systems

**v2.1 (Previous)**
- ✅ Excel-to-JSON audio management system
- ✅ Multi-model AI support (Groq/OpenAI/Gemini)
- ✅ Audio optimization and compression
- ✅ Comprehensive logging system

## 🚀 Roadmap

### **Phase 3 Features (In Progress)**
- [ ] **Regional Language Support** - Hindi TTS with Indian voice models
- [ ] **Advanced Call Analytics** - Sentiment analysis and conversion tracking
- [ ] **CRM Integration** - Salesforce, HubSpot direct sync
- [ ] **Multi-agent Conversations** - AI agents talking to each other

### **Phase 4 Features (Future)**
- [ ] **Voice Cloning** - Custom voice models for each client
- [ ] **Real-time Coaching** - Live suggestions during calls
- [ ] **Predictive Dialing** - AI-powered lead scoring and timing
- [ ] **WhatsApp Integration** - Follow-up messages and scheduling

## 📚 Onboarding Guide for New Team Members

### **For Prompt Engineers**
1. **Understand the audio flow**: Pre-recorded snippets vs TTS fallback
2. **Study `router.py`**: Learn how AI matches user input to audio files
3. **Practice with Excel**: Update `audio_files.xlsx` and test changes
4. **Test different scenarios**: Ensure comprehensive coverage of user inputs

### **For Python Developers**
1. **Study the architecture**: Main components and data flow
2. **Understand PCM format**: Why telephony systems need specific audio formats
3. **Learn WebSocket handling**: How real-time audio streaming works
4. **Practice debugging**: Use debug commands and log analysis

### **For Content Teams**
1. **Master Excel workflow**: How to add/update audio content
2. **Understand categories**: How to organize audio files logically
3. **Learn quality standards**: Recording quality and transcript accuracy
4. **Test your changes**: Always verify updates work before deploying

### **For Operations Teams**
1. **Monitor system health**: Use debug endpoints and log analysis
2. **Understand metrics**: Response times, cache hit rates, error rates
3. **Learn troubleshooting**: Common issues and resolution steps
4. **Track performance**: Monitor call success rates and user satisfaction

## 📄 Patent Information

This system implements our **"Modular Voice Response System with Dynamic Audio Assembly and Fallback AI Generation"** patent (pending). Key innovations:

- **Memory-cached PCM audio library** with instant AI selection
- **Hybrid audio system** with intelligent fallback to TTS
- **Session memory management** to prevent repetitive responses  
- **Ultra-low latency architecture** with direct audio streaming
- **Format-agnostic compatibility** with automatic conversion

## 🤝 Contributing

### **Hiring Checklist for New Team Members**

**Technical Roles:**
1. **Python/Flask Experience** - WebSocket, API integration, audio processing
2. **Telephony Knowledge** - Understanding of PCM, audio formats, streaming
3. **AI/ML Familiarity** - LLM integration, prompt engineering, model selection
4. **Audio Processing** - librosa, numpy, format conversion experience

**Non-Technical Roles:**
1. **Excel Proficiency** - Comfortable with spreadsheets and data entry
2. **Audio Production** - Recording quality, transcript accuracy
3. **Testing Mindset** - Systematic verification of changes
4. **Documentation Skills** - Clear communication of processes

## 📞 Support & Escalation

### **Self-Service Resources**
- **Debug Endpoints**: `/debug/system_health`, `/exotel/debug`
- **Log Files**: `logs/call_logs.csv`, `logs/conversation_logs.csv`
- **Test Interface**: `/test` (browser-based testing)

### **Escalation Path**
1. **Level 1**: Check logs and debug endpoints
2. **Level 2**: Run diagnostic commands from troubleshooting section
3. **Level 3**: Check API quotas and service status
4. **Level 4**: Contact technical lead with specific error messages

---

**Built with ❤️ by the Klariqo Team**

*Revolutionizing voice AI with patent-pending PCM streaming technology*