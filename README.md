# AI Ticket Supporter - Intelligent Support Ticket Routing System

A production-grade AI-powered support ticket analysis and routing system with real-time speech-to-text, multi-language support, and intelligent guidance generation.

## Features

### 🎙️ Speech-to-Text
- Click microphone button to speak your issue
- Real-time speech recognition (works in Chrome, Edge, Safari)
- Text automatically appears in textarea as you speak
- No API needed - works offline

### 🌐 Multi-Language Support
- **9 Indian Languages:** Hindi, Tamil, Telugu, Kannada, Malayalam, Gujarati, Marathi, Bengali, Punjabi
- Dynamic translation of guidance and email responses
- Single language dropdown controls both sections
- Real-time translation without page reload

### 🤖 AI-Powered Analysis
- **BART** (facebook/bart-large-mnli): Zero-shot ticket classification
- **Mistral-7B**: Dynamic troubleshooting guidance generation
- **Llama-2**: Customer response email generation
- **Llama-3.1**: Quality assessment scoring

### 🛠️ Intelligent Guidance
- Context-aware troubleshooting steps based on exact issue
- Different guidance for "charged twice" vs "refund" vs "missing charge"
- Different steps for "app crash" vs "app slow" vs "app error"
- Tailored recovery steps for different account access problems

### 📊 Comprehensive Analysis
- Category classification (Billing, Technical, Account Access, Product Question, General)
- Urgency detection (Urgent, High, Medium, Low)
- Sentiment analysis (Positive, Neutral, Negative)
- Issue complexity and severity assessment
- Automatic routing decision to appropriate team

### 🔒 Security
- PII detection and masking (emails, phone, SSN, credit cards, etc.)
- PII warning before processing
- Secure ticket handling with automatic masking
- Rate limiting to prevent abuse

### 📧 Email Generation
- Dynamic customer response emails adapted to ticket context
- Sentiment-aware greetings
- Urgency-based response time commitments
- Automatic team routing information

## Tech Stack

**Frontend:**
- React 18 with Vite
- CSS3 with dark/light theme support
- Web Speech API for speech recognition
- MyMemory API for translations

**Backend:**
- Flask (Python)
- PostgreSQL database
- Hugging Face Inference API
- Multi-model LLM orchestration

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL running locally
- HuggingFace API token (free at huggingface.co)

### Setup

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
Create `.env` file in `backend/`:
```
HF_API_TOKEN=your_token_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_ticket_support
FLASK_ENV=development
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

### Run

**Backend:**
```bash
cd backend
FLASK_APP=app.py python -m flask run --port 5001
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173`

## Usage

1. **Submit Ticket:**
   - Type or use 🎙️ microphone to describe issue
   - System detects PII and warns you
   - Click "Analyze & Route"

2. **View Results:**
   - Modal shows comprehensive analysis
   - 🔀 Routing decision and assigned team
   - 🛠️ Dynamic troubleshooting steps
   - 📧 Customer response email
   - ⭐ Quality scores

3. **Change Language:**
   - Click language dropdown
   - Select any Indian language
   - Guidance AND email translate together
   - Switch anytime without reloading

## File Structure

```
AI_TicketSupporter/
├── backend/
│   ├── app.py                 # Flask application
│   ├── config.py              # Configuration
│   ├── requirements.txt        # Python dependencies
│   ├── routes/
│   │   └── ticket_routes.py    # API endpoints
│   ├── services/
│   │   └── ticket_processing_service.py
│   ├── utils/
│   │   ├── multi_model_client.py      # LLM orchestration
│   │   ├── pii_detector.py             # Security
│   │   ├── translation_service.py      # Translation
│   │   └── ...
│   └── prompts/
│       └── prompt_templates.py
└── frontend/
    ├── src/
    │   ├── App.jsx            # Main component
    │   ├── App.css            # Styling
    │   ├── ResultsModal.jsx    # Results display
    │   └── ...
    ├── package.json
    └── vite.config.js
```

## API Endpoints

- `POST /api/ticket` - Submit and analyze ticket
- `POST /api/translate` - Translate text to Indian languages

## Performance

- **Average Processing:** 3-8 seconds
- **Models Used:** 4 specialized LLMs
- **Concurrency:** Rate limited (100 req/min global, 10 req/min per ticket)
- **Caching:** 24-hour cache for duplicate tickets

## Models

| Model | Purpose | Size |
|-------|---------|------|
| BART | Classification | Large |
| Mistral-7B | Guidance Generation | 7B params |
| Llama-2 | Email Generation | 7B params |
| Llama-3.1 | Quality Assessment | 8B params |

## Language Support

- English (original)
- हिंदी (Hindi)
- தமிழ் (Tamil)
- తెలుగు (Telugu)
- ಕನ್ನಡ (Kannada)
- മലയാളം (Malayalam)
- ગુજરાતી (Gujarati)
- मराठी (Marathi)
- বাংলা (Bengali)
- ਪੰਜਾਬੀ (Punjabi)

## Browser Support

- Chrome/Chromium (Best)
- Edge
- Safari
- Opera
- Firefox (Limited speech-to-text)

## License

MIT
