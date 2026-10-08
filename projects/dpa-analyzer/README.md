# DPA Privacy Legal Review AI Agent

An AI-powered tool for automated privacy legal review of Data Processing Agreements (DPAs) with GDPR compliance analysis.

## 🚀 Features

- **AI-Powered Analysis**: Uses open source LLMs (via Ollama) for comprehensive DPA review
- **Comprehensive Playbook**: Built-in knowledge base with DPA review best practices
- **Modern Web Interface**: Clean, responsive UI for document upload and analysis
- **Structured Analysis**: Detailed compliance scoring and risk assessment
- **GDPR Compliance**: Focused on GDPR Article 28 requirements and privacy best practices
- **Document Support**: PDF, DOC, DOCX, and TXT file formats

## 📋 Prerequisites

Before running the application, ensure you have:

1. **Python 3.8+** installed
2. **Ollama** installed and running (for LLM functionality)
3. **Modern web browser** for the frontend

## 🔧 Installation & Setup

### Step 1: Install Ollama and Download Model

1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Download a suitable model (recommended: Llama 3.1 8B):
   ```bash
   ollama pull llama3.1:8b
   ```
3. Start Ollama server:
   ```bash
   ollama serve
   ```

### Step 2: Set Up Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   python main.py
   ```
   
   The backend will be available at `http://localhost:8000`

### Step 3: Set Up Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start a simple HTTP server:
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Or using Node.js (if you have it)
   npx serve . -p 3000
   ```

3. Open your browser and go to `http://localhost:3000`

## 🎯 Usage

### Analyzing a DPA Document

1. **Upload Document**: Drag and drop or click to select a DPA document (PDF, DOC, DOCX, or TXT)
2. **Start Analysis**: Click "Analyze Document" to begin the AI review process
3. **Review Results**: Examine the comprehensive analysis including:
   - Overall compliance score and risk level
   - Section-by-section analysis
   - Critical issues and recommendations
   - Strengths and missing clauses

### Understanding the Analysis

The tool provides analysis across 10 key areas:
- **Parties and Roles**: Data controller/processor identification
- **Purpose and Scope**: Processing purposes and data categories
- **Data Subject Rights**: Rights fulfillment procedures
- **Security Measures**: Technical and organizational safeguards
- **International Transfers**: Cross-border transfer mechanisms
- **Subprocessing**: Subprocessor management
- **Data Retention**: Retention and deletion procedures
- **Breach Notification**: Incident response procedures
- **Auditing and Compliance**: Audit rights and monitoring
- **Liability**: Liability allocation and indemnification

### Viewing the Playbook

Click "View Playbook" to access the comprehensive DPA review guide that includes:
- Best practices for each review section
- Key points to verify
- Red flags to watch for
- GDPR compliance requirements

## 🏗️ Architecture

```
DPA Legal Review AI/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application server
│   ├── dpa_analyzer.py     # AI analysis engine
│   ├── knowledge_base.py   # DPA review playbook
│   └── requirements.txt    # Python dependencies
├── frontend/               # Web interface
│   ├── index.html         # Main page
│   ├── styles.css         # Modern styling
│   └── script.js          # Interactive functionality
└── README.md              # This file
```

## 🤖 AI Model Configuration

The system is configured to use Llama 3.1 8B by default, but you can modify the model in `backend/dpa_analyzer.py`:

```python
self.model_name = "llama3.1:8b"  # Change to your preferred model
```

Supported models include:
- `llama3.1:8b` (recommended for balance of speed and quality)
- `llama3.1:70b` (higher quality, requires more resources)
- `mistral:7b` (faster, good for basic analysis)
- `mixtral:8x7b` (good performance balance)

## 🔍 API Endpoints

- `GET /` - Health check
- `GET /playbook` - Retrieve DPA review playbook
- `POST /analyze-dpa` - Analyze uploaded DPA document
- `GET /analysis-template` - Get analysis result structure

## ⚠️ Important Notes

### Legal Disclaimer
This tool provides automated analysis for educational and MVP purposes only. **Always consult with qualified legal professionals for final review and legal advice.** The AI analysis should supplement, not replace, human legal expertise.

### Limitations
- AI analysis quality depends on the selected model and document quality
- Fallback rule-based analysis is used if LLM is unavailable
- Document text extraction may vary based on file format and quality
- Analysis is focused on GDPR compliance; other jurisdictions may have different requirements

### Privacy & Security
- Documents are processed locally and not stored permanently
- No document content is sent to external services (except local Ollama)
- Consider data sensitivity when analyzing confidential agreements

## 🛠️ Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is downloaded: `ollama list`
   - Verify Ollama is accessible at `http://localhost:11434`

2. **Backend Errors**
   - Check Python version (3.8+ required)
   - Ensure all dependencies are installed
   - Verify virtual environment is activated

3. **Frontend Not Loading**
   - Check if backend is running on port 8000
   - Verify CORS settings in backend
   - Try a different port for frontend

4. **Analysis Fails**
   - Check document format (PDF, DOC, DOCX, TXT only)
   - Ensure file size is under 10MB
   - Verify document contains readable text

## 🔄 Development

To extend or modify the system:

1. **Add New Analysis Sections**: Modify the playbook in `knowledge_base.py`
2. **Improve AI Prompts**: Update prompts in `dpa_analyzer.py`
3. **Enhance UI**: Modify frontend files for better user experience
4. **Add New File Types**: Extend document processing in the analyzer

## 📝 License

This project is developed for educational and MVP purposes. Use responsibly and ensure compliance with applicable laws and regulations.

## 🤝 Contributing

This is an MVP project. For production use, consider:
- Enhanced error handling and logging
- User authentication and session management
- Document storage and history
- Integration with legal document management systems
- Advanced AI model fine-tuning for legal domain
- Multi-language support
- Batch processing capabilities
