# RouteLLM 🚀

### Intelligent Multi-Model AI Router

RouteLLM is an AI-powered multi-model routing system that intelligently analyzes user requests and selects the most suitable AI model or specialized service for the task.

Instead of sending every request to a single LLM, RouteLLM uses an intelligent routing layer to distribute tasks across specialized models for **coding, general reasoning, web research, image understanding, document OCR, and speech transcription**.

---

## 🧠 How It Works

```text
                    ┌──────────────────┐
                    │      USER        │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌──────────────────────┐
                 │   RouteLLM Router    │
                 │   GPT-OSS 120B       │
                 └──────────┬───────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     ┌──────────┐     ┌──────────┐      ┌──────────┐
     │  CODING  │     │ GENERAL  │      │   WEB    │
     └────┬─────┘     └────┬─────┘      └────┬─────┘
          │                │                 │
          ▼                ▼                 ▼
       Qwen 3.6        GPT-OSS 20B        Tavily
       27B                              + GPT-OSS
          │                │                 │
          └────────────────┼─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   RESPONSE   │
                    └──────────────┘


Additional Multimodal Services:

Image  ──────────► Qwen 3.6 27B
Documents ───────► Mistral OCR
Audio ────────────► Whisper Large V3 Turbo
```

---

## ✨ Key Features

### 🤖 Intelligent Model Routing

Uses a dedicated routing model to classify text requests and automatically select the appropriate specialist.

Routes include:

* **CODING** → Qwen 3.6 27B
* **GENERAL** → GPT-OSS 20B
* **WEB** → Tavily + GPT-OSS

The router also returns a **confidence score** for its routing decision.

### 💻 Coding Specialist

Programming-related requests are automatically routed to Qwen 3.6 27B.

Supports:

* Code generation
* Debugging
* Algorithms
* Data structures
* APIs
* Databases
* Software engineering questions

### 🌐 Web Research

For information that may change over time, RouteLLM can perform web searches using Tavily and pass the retrieved information to an LLM for synthesis.

This enables:

* Current information retrieval
* Web research
* Recent events
* Current products and companies
* Source-based answers

### 👁️ Image Understanding

RouteLLM supports image analysis using a multimodal LLM.

Users can provide an image and ask questions about its contents.

### 📄 Document OCR

Documents and images can be processed using Mistral OCR.

Supported formats:

* PDF
* PNG
* JPG
* JPEG
* WEBP

### 🎙️ Speech-to-Text

Audio files can be transcribed using Whisper Large V3 Turbo.

### 🧠 Conversation Memory

RouteLLM maintains local conversation history using a simple `history.txt` file.

Recent conversation history can be supplied to the routing and response models to maintain context.

### ⚡ Response Metrics

The system tracks processing time for different operations, making it easier to evaluate routing and model performance.

---

## 🏗️ Architecture

```text
                         RouteLLM
                            │
                            ▼
                   ┌─────────────────┐
                   │ Routing Engine  │
                   │   GPT-OSS 120B  │
                   └────────┬────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
          Coding         General          Web
             │              │              │
             ▼              ▼              ▼
          Qwen 3.6       GPT-OSS 20B      Tavily
           27B                             │
                                           ▼
                                      GPT-OSS 20B

             Multimodal Processing
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Image        OCR          Audio
        │            │            │
        ▼            ▼            ▼
      Qwen        Mistral       Whisper
      3.6 27B       OCR           V3
```

---

## 🛠️ Tech Stack

| Technology             | Purpose                       |
| ---------------------- | ----------------------------- |
| Python                 | Core application              |
| Groq                   | LLM inference                 |
| GPT-OSS 120B           | Intelligent routing           |
| Qwen 3.6 27B           | Coding & vision               |
| GPT-OSS 20B            | General reasoning & synthesis |
| Mistral OCR            | Document/image OCR            |
| Whisper Large V3 Turbo | Speech-to-text                |
| Tavily                 | Web search                    |
| python-dotenv          | Environment configuration     |

---

## 📁 Project Structure

```text
RouteLLM/
│
├── main.py
├── history.txt
├── .env
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/RouteLLM.git
cd RouteLLM
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -U groq mistralai tavily-python python-dotenv
```

### 4. Configure API Keys

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
MISTRAL_API_KEY=your_mistral_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 5. Run

```bash
python main.py
```

---

## 🎮 Available Commands

```text
Normal text
    Type your question directly

/image
    Analyze an image

/ocr
    Extract text from a PDF or image

/audio
    Transcribe an audio file

/web
    Perform a web search

/history
    View conversation history

/clear
    Clear conversation history

/help
    Show available commands

/exit
    Exit RouteLLM
```

---

## 🔀 Example Routing

### Coding Request

```text
You: Write a Java program for binary search
```

```text
Router selected: CODING
Confidence: 98%

→ Qwen 3.6 27B
```

### General Request

```text
You: Explain quantum computing in simple words
```

```text
Router selected: GENERAL
Confidence: 96%

→ GPT-OSS 20B
```

### Current Information

```text
You: What are the latest developments in AI?
```

```text
Router selected: WEB
Confidence: 94%

→ Tavily
→ GPT-OSS 20B
```

---

## 🎯 Why RouteLLM?

Traditional AI applications often rely on a single model for every task.

RouteLLM takes a different approach:

```text
One Request
     ↓
Understand the Task
     ↓
Select the Specialist
     ↓
Process the Request
     ↓
Return the Response
```

This architecture makes it possible to build AI systems where different models and tools can specialize in different types of workloads.

---

## 📊 Multimodal Capabilities

| Input        | Processing                  | Technology             |
| ------------ | --------------------------- | ---------------------- |
| Text         | Intelligent Routing         | GPT-OSS 120B           |
| Code         | Code Generation & Reasoning | Qwen 3.6 27B           |
| General Text | Reasoning                   | GPT-OSS 20B            |
| Web Query    | Search + Synthesis          | Tavily + GPT-OSS       |
| Image        | Vision Analysis             | Qwen 3.6 27B           |
| PDF          | OCR                         | Mistral OCR            |
| Image        | OCR                         | Mistral OCR            |
| Audio        | Transcription               | Whisper Large V3 Turbo |

---

## 🔐 Security

API credentials are loaded through environment variables.

Do not commit your `.env` file.

Recommended `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
history.txt
```

---

## 🚀 Future Improvements

Potential extensions include:

* FastAPI backend
* Web-based frontend
* Streaming responses
* Authentication
* Persistent database memory
* Model cost tracking
* Latency benchmarking
* Route analytics
* Automatic fallback models
* Routing based on cost, latency, and quality
* User-configurable routing policies
* Docker deployment
* Cloud deployment
* Model performance evaluation

---

## 💡 Project Highlights

RouteLLM demonstrates practical implementation of:

* Multi-LLM orchestration
* Intelligent model routing
* Multimodal AI
* Tool calling and external APIs
* Web-grounded generation
* OCR pipelines
* Speech-to-text
* Conversation memory
* AI system architecture
* API integration

---

## 📌 Project Status

**Current Status:** Functional CLI prototype

The current implementation provides intelligent text routing along with image analysis, OCR, web research, speech transcription, and local conversation memory.

---

## 👨‍💻 Author

**Your Name**

Built as a practical exploration of **Generative AI, LLM orchestration, multimodal AI, and intelligent model routing**.

---

## ⭐ If You Find This Interesting

Star the repository and feel free to explore, modify, and extend RouteLLM.
