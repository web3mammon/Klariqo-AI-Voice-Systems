# 🚀 Klariqo School System v2.0

**AI-Powered Voice Sales Agent for Schools** | Ultra-Fast Streaming | Patent-Pending Technology

Klariqo uses our revolutionary **Modular Voice Response System** to create the most human-sounding AI voice agents that sell your product while you sleep. This implementation specifically targets school principals to pitch Klariqo's voice AI services.

## 🆕 **Version 2.0 - Major Updates**

### **🎵 Audio Management Revolution**
- **Excel-to-JSON Converter** - Manage all audio files via simple Excel spreadsheet
- **Automatic File Discovery** - System dynamically finds and validates audio files
- **Alternate Version Support** - Multiple versions of same content for natural variation
- **Ultra-Compressed Audio** - 75% smaller files (14MB → 3.6MB) for lightning-fast loading

### **🤖 AI Engine Flexibility**
- **Multi-Model Support** - Switch between Groq (Llama), OpenAI (GPT-3.5/4), or Claude
- **Smart File Selection** - AI automatically chooses between alternate versions
- **Structured Prompting** - Rule-based responses with intelligent fallbacks
- **Dynamic Context** - AI sees available files and makes smart choices

### **📊 Enterprise Features** 
- **Comprehensive Logging** - Every call tracked in CSV format
- **Session Management** - Handles concurrent calls with isolated state
- **Hot Reloading** - Update audio library without system restart
- **Debug Endpoints** - System health monitoring and troubleshooting

## 🎯 What This Does

- **Nisha** (our AI agent) calls school principals to pitch Klariqo
- Handles both **inbound** (demo calls) and **outbound** (cold calls) 
- Uses pre-recorded audio snippets for ultra-fast, human-like responses
- **Smart AI selection** between multiple file versions for natural variation
- Falls back to real-time TTS only when needed
- **Excel-driven content management** for easy updates
- Logs every conversation for analysis and improvement
- **Multi-model AI support** (Groq, OpenAI, Claude)

## 🏗️ Architecture

```
├── main.py                 # Application runner & WebSocket handler
├── config.py              # Centralized configuration management  
├── session.py             # Call session state management
├── router.py              # AI-powered response selection (Multi-model support)
├── audio_manager.py       # Audio file library management with Excel integration
├── tts_engine.py          # ElevenLabs TTS fallback
├── logger.py              # Structured call logging to CSV
├── routes/
│   ├── inbound.py         # Inbound call handlers
│   ├── outbound.py        # Outbound call & campaign management
│   └── test.py            # Testing & debug endpoints
├── audio/                 # Original high-quality audio files
├── audio_optimised/       # Ultra-compressed audio (auto-used by system)
├── logs/                  # Call logs and conversation transcripts
├── temp/                  # Temporary TTS generated files
├── audio_snippets.json    # Auto-generated from Excel (don't edit manually)
├── audio_files.xlsx       # YOUR MAIN AUDIO MANAGEMENT FILE
├── excel_to_json.py       # Excel to JSON converter script
├── optimize_audio.py      # Audio compression utility
├── .env                   # Environment variables & API keys
└── requirements.txt       # Python dependencies
```

## 📋 Prerequisites

1. **Python 3.8+** 
2. **API Accounts:**
   - [Twilio](https://twilio.com) - Voice calling
   - [Deepgram](https://deepgram.com) - Speech-to-Text
   - [Groq](https://groq.com) - Ultra-fast LLM
   - [ElevenLabs](https://elevenlabs.io) - Text-to-Speech
3. **ngrok** - For local development webhooks

## 🚀 Quick Setup

### 1. Clone & Install
```bash
git clone <your-repo>
cd klariqo-school-system
pip install -r requirements.txt
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
GROQ_API_KEY=your_groq_key              # Ultra-fast Llama (50-100ms)
OPENAI_API_KEY=your_openai_key          # Reliable GPT-3.5/4 (200-500ms)  

# Twilio Voice Services
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE=+1234567890
```

### 3. Prepare Audio Files & Excel Management

**NEW: Excel-Based Audio Management**
```bash
# Create your audio management Excel file
# Columns: Filename | Transcript | Category | Alternate_Version

# Convert Excel to JSON
python excel_to_json.py

# Your audio files structure:
mkdir audio                    # Original high-quality files  
mkdir audio_optimised         # Ultra-compressed versions (auto-used)
mkdir temp                    # Temporary TTS files
mkdir logs                    # Call logs and analytics
```

**Excel Structure Example:**
| Filename | Transcript | Category | Alternate_Version |
|----------|------------|----------|-------------------|
| intro_klariqo1.1.mp3 | नमस्ते! मैं निशा... | introductions | intro_klariqo1.2.mp3 |
| pricing1.1.mp3 | हमारी pricing... | pricing | pricing1.2.mp3 |

**Benefits:**
- ✅ **Easy Updates** - Just edit Excel and re-run converter
- ✅ **Version Management** - Automatic handling of alternate files  
- ✅ **No JSON Errors** - Perfect formatting every time
- ✅ **Team Friendly** - Non-technical team members can update content

### 4. Run the System
```bash
python main.py
```

The system will:
- ✅ Validate configuration
- 🌐 Start ngrok tunnel (for webhooks)
- 📞 Display webhook URLs for Twilio
- 🧪 Provide test page URL

## 🧪 Testing

### Browser Testing
1. Go to `http://your-ngrok-url/test`
2. Click "Call +919876543210" (update with your number)
3. Answer the call and pretend to be a school principal
4. Experience Nisha pitching Klariqo!

### API Testing
```bash
# Start outbound campaign
curl -X POST http://your-ngrok-url/outbound/start_campaign

# Check campaign status  
curl http://your-ngrok-url/outbound/campaign_status

# View system health
curl http://your-ngrok-url/debug/system_health
```

## 🎵 Audio File Management (NEW!)

### **Excel-Based Workflow**

**Create `audio_files.xlsx` with columns:**
- **Filename** - MP3 file names (e.g., `intro_klariqo1.1.mp3`)
- **Transcript** - What Nisha says in this file
- **Category** - File organization (auto-guessed if blank)  
- **Alternate_Version** - Alternative version filename (optional)

### **Convert Excel to JSON**
```bash
python excel_to_json.py
# Choose option 1 to convert
```

### **Audio Optimization**
```bash
python optimize_audio.py
# Converts audio/ → audio_optimised/ (75% smaller files)
```

### **Adding New Audio Files**
1. **Record new MP3** and save to `audio/` folder
2. **Add row to Excel** with filename + transcript
3. **Run converter:** `python excel_to_json.py`
4. **Optimize audio:** `python optimize_audio.py` 
5. **Restart system:** `python main.py`

### **Alternate Versions**
Perfect for natural conversation variety:
```
Filename: intro_klariqo1.1.mp3
Alternate_Version: intro_klariqo1.2.mp3
→ AI randomly chooses between versions
```

## 📊 Logging & Analytics

### Call Logs
- `logs/call_logs.csv` - Summary of each call
- `logs/conversation_logs.csv` - Detailed conversation turns

### View Statistics
```bash
# Get recent stats via API
curl http://your-ngrok-url/debug/call_logs

# Or view in browser
http://your-ngrok-url/debug/call_logs
```

## 🤖 AI Model Configuration

### **Switch Between AI Models**
Update `router.py` to use different models:

**Groq (Llama) - Ultra Fast:**
```python
from groq import Groq
client = Groq(api_key=Config.GROQ_API_KEY)
model = "llama-3.1-8b-instant"  # ~50-100ms response
```

**OpenAI (GPT) - Most Reliable:**
```python
from openai import OpenAI  
client = OpenAI(api_key=Config.OPENAI_API_KEY)
model = "gpt-3.5-turbo"  # ~200-500ms response
```

### **Model Comparison**
| Model | Speed | Reliability | Cost/1M tokens | Best For |
|-------|-------|-------------|----------------|----------|
| Llama-3.1-8b | 🚀 50-100ms | ⭐⭐⭐ | $0.10 | Speed-critical |
| GPT-3.5-turbo | ⚡ 200-500ms | ⭐⭐⭐⭐⭐ | $0.50 | Reliability |
| GPT-4o | 🐌 500-1000ms | ⭐⭐⭐⭐⭐ | $2.50 | Complex logic |

## 🔧 Customization

### For Different Industries
1. Update `audio_snippets.json` with new industry content
2. Modify the system prompt in `router.py`
3. Update lead data structure in `routes/outbound.py`
4. Customize session memory flags in `config.py`

### Adding New Features
- **CRM Integration**: Extend `logger.py` 
- **WhatsApp Follow-ups**: Add webhook in `routes/`
- **Advanced Analytics**: Enhance `logger.py` with metrics
- **Multi-language**: Update Deepgram config in `config.py`

## 🛠️ Production Deployment

### Environment Setup
1. Use a proper web server (nginx + gunicorn)
2. Set up SSL certificates for webhooks
3. Use environment-specific `.env` files
4. Enable production logging levels

### Scaling Considerations
- Deploy multiple instances for high call volume
- Use Redis for session management across instances  
- Implement proper error handling and retry logic
- Set up monitoring and alerting

### Security
- Never commit `.env` files
- Use IAM roles instead of hardcoded API keys
- Implement webhook signature validation
- Regular security audits of dependencies

## 📞 Twilio Configuration

### Webhook URLs
Set these in your Twilio Console:

**For Inbound Calls:**
- Webhook URL: `https://your-domain.com/twilio/voice`
- HTTP Method: POST

**For Outbound Calls:**
- Configured automatically via API calls

### Phone Number Setup
1. Buy a Twilio phone number
2. Configure it for voice
3. Set webhook URL to your inbound endpoint
4. Update `TWILIO_PHONE` in `.env`

## 🐛 Troubleshooting

### Common Issues

**"No audio files found"**
- Check `audio/` folder exists
- Verify file names match `audio_snippets.json`
- Ensure MP3 format and proper encoding

**"API key errors"**  
- Verify all keys in `.env` are correct
- Check API account quotas/limits
- Test individual services separately

**"Webhook not receiving calls"**
- Confirm ngrok is running
- Check Twilio webhook configuration
- Verify firewall/network settings

**"TTS generation failed"**
- Check ElevenLabs API quota
- Verify voice ID is correct
- Test TTS endpoint separately

### Debug Commands
```bash
# Test individual components
python -c "from tts_engine import tts_engine; tts_engine.test_voice()"
python -c "from audio_manager import audio_manager; print(len(audio_manager.cached_files))"

# View detailed logs
tail -f logs/call_logs.csv
tail -f logs/conversation_logs.csv
```

## 📈 Performance Metrics & Updates

### **Version 2.0 Benchmarks**
- **Audio Loading**: 75% faster (14MB → 3.6MB files)
- **Response Latency**: 200-500ms total (vs 700-1000ms traditional)
- **File Management**: 90% easier (Excel vs manual JSON editing)
- **AI Reliability**: 95%+ accuracy with structured prompting
- **Natural Variation**: Automatic via alternate file versions

### **Recent Major Updates**

**v2.1 (Current)**
- ✅ Excel-to-JSON audio management system
- ✅ Multi-model AI support (Groq/OpenAI/Claude)
- ✅ Alternate file version handling
- ✅ Ultra-compressed audio optimization
- ✅ Comprehensive logging system

**v2.0 (Base)**
- ✅ Modular architecture with clean separation
- ✅ Session management for concurrent calls
- ✅ Twilio integration with WebSocket streaming
- ✅ Patent-pending audio snippet system

## 🚀 Roadmap

### Phase 2 Features (In Progress)
- [ ] **Voice-enabled AI collaboration platform** - Claude + GPT + Human team calls
- [ ] **Real-time audio streaming optimization** - Sub-100ms response times
- [ ] **Advanced campaign management** - CRM integration with lead scoring
- [ ] **Multi-language expansion** - Regional Indian language support

### Phase 3 Features  
- [ ] **AI-to-AI autonomous conversations** - Self-optimizing sales strategies
- [ ] **Integration ecosystem** - Salesforce, HubSpot, WhatsApp Business
- [ ] **Advanced analytics** - Conversation sentiment and success prediction
- [ ] **White-label platform** - Deploy for other industries instantly

### **🦄 Vision: The Future of Work**
Building toward an **AI-native company operations platform** where human-AI teams collaborate seamlessly through voice, chat, and task management - potentially bigger than Klariqo itself!

## 📄 Patent Information

This system implements our **"Modular Voice Response System with Dynamic Audio Assembly and Fallback AI Generation"** patent (pending). Key innovations:

- Pre-recorded audio snippet library with AI selection
- Intelligent fallback to TTS only when needed
- Session memory to prevent repetitive responses  
- Ultra-low latency response architecture

## 🤝 Contributing

When hiring new team members:

1. **Developers**: Focus on Python/Flask, WebSocket, and API integration experience
2. **Voice Engineers**: Audio production, ElevenLabs, voice cloning expertise  
3. **Sales**: Understanding of B2B sales, school market knowledge
4. **Operations**: Call center management, data analysis skills

## 📞 Support

- **Technical Issues**: Check logs in `/debug/` endpoints
- **Business Questions**: Review conversation logs for insights
- **Feature Requests**: Submit via GitHub issues
- **Emergency**: Monitor system health via `/debug/system_health`

---

**Built with ❤️ by the Klariqo Team**

*Revolutionizing voice AI, one conversation at a time.*