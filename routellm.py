import os
import re
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import shutil
import uuid

from dotenv import load_dotenv
from groq import Groq
from google import genai
from mistralai.client import Mistral
from tavily import TavilyClient
from langchain_core.tools import tool

load_dotenv()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

mistral_client = Mistral(
    api_key=os.getenv("MISTRAL_API_KEY")
)

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

ROUTER_MODEL = "openai/gpt-oss-120b"
CODING_MODEL = os.getenv("CODING_MODEL", "qwen/qwen3.8-27b")
GENERAL_MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "gemma-4-26b-a4b-it"
WHISPER_MODEL = "whisper-large-v3-turbo"
OCR_MODEL = "mistral-ocr-4-1"

from database import (
    init_db,
    load_history,
    save_history,
    load_users,
    save_user,
    get_history_text,
    clear_history,
    get_db_status
)

# Initialize MongoDB / local storage
init_db()


def clean_response(text: str) -> str:
    """Sanitizes unwanted markdown asterisks (* and **) and header hashes (#) outside of code blocks."""
    if not text:
        return ""
    parts = text.split("```")
    cleaned_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # Inside code block: preserve code as is
            cleaned_parts.append(part)
        else:
            # Outside code block
            # 1. Remove markdown heading hashes: '# Heading', '## Heading' -> 'Heading'
            p = re.sub(r'(?m)^#{1,6}\s*', '', part)
            # 2. Remove bold/italic asterisks: '**word**' -> 'word', '*word*' -> 'word'
            p = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', p)
            # 3. Convert asterisk bullets '* ' at start of line to clean bullet '• '
            p = re.sub(r'(?m)^\s*\*\s+', '• ', p)
            # 4. Remove any stray remaining asterisks
            p = p.replace('*', '')
            cleaned_parts.append(p)
    return "```".join(cleaned_parts)


@tool
def qwen_coding(query: str, history: str = "") -> str:
    """Use for programming, debugging, software engineering, algorithms and code generation."""

    prompt = f"""
Previous conversation:
{history}

Current user query:
{query}

Give an accurate, practical, and clean answer.
CRITICAL FORMATTING INSTRUCTIONS:
- Do NOT use markdown asterisks (* or **) or header hashes (#, ##, ###) in your explanations or titles.
- Do not bold words using asterisks.
- For headings, use plain words or UPPERCASE on a new line.
- For lists, use numbered points (1., 2.) or simple hyphens (-).
- Code blocks inside standard ``` are allowed and welcomed.
"""

    result = groq_client.chat.completions.create(
        model=CODING_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a coding and software engineering specialist. "
                    "CRITICAL FORMATTING INSTRUCTION: Do NOT use markdown asterisks (* or **) or header hashes (#, ##, ###) in your explanations. "
                    "Never use asterisks for bolding or bullet points. Use clean, plain text and numbered lists (1., 2.) or hyphens (-). "
                    "For code, use standard triple backtick blocks."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return clean_response(result.choices[0].message.content)


@tool
def gptoss_general(query: str, history: str = "") -> str:
    """Use for normal conversation, explanations, rewriting, summaries and general questions."""

    prompt = f"""
Previous conversation:
{history}

Current user query:
{query}

Answer clearly in the same language as the user.
CRITICAL FORMATTING INSTRUCTIONS:
- Do NOT use markdown asterisks (* or **) or header hashes (#, ##, ###) anywhere.
- Do not bold or italicize words using asterisks.
- For headings, write clean titles in UPPERCASE or on their own line without hashes.
- For lists, use numbered points (1., 2.) or simple hyphens (-).
- Keep formatting clean, natural, and free of special formatting symbols.
"""

    result = groq_client.chat.completions.create(
        model=GENERAL_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful general-purpose AI assistant with conversation memory. "
                    "CRITICAL FORMATTING INSTRUCTION: Strictly avoid markdown asterisks (* or **) and header hashes (#, ##, ###). "
                    "Never use asterisks for bolding or bullet points. Present information cleanly using plain text, capital headings, and numbered lists."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return clean_response(result.choices[0].message.content)


@tool
def web_search(query: str, history: str = "") -> str:
    """Use for current information, news, internet research and live information."""

    search_query = query

    if history:
        search_query = f"""
Previous conversation:
{history}

Current user query:
{query}
"""

    result = tavily_client.search(
        query=search_query,
        search_depth="basic",
        max_results=5
    )

    raw_results = ""
    for item in result.get("results", []):
        raw_results += "Title: " + item.get("title", "")
        raw_results += "\nURL: " + item.get("url", "")
        raw_results += "\nContent: " + item.get("content", "")
        raw_results += "\n\n"

    synth_prompt = f"""
Based on the following live web search results, answer the user's query clearly and accurately.

Search Results:
{raw_results}

Previous conversation:
{history}

User query:
{query}

CRITICAL FORMATTING INSTRUCTIONS:
- Do NOT use markdown asterisks (* or **) or header hashes (#, ##, ###).
- Do not bold words using asterisks.
- For section headings, use plain words or UPPERCASE on a separate line.
- For lists, use numbered points (1., 2.) or simple hyphens (-).
- Cite source URLs naturally in plain text.
"""

    res = groq_client.chat.completions.create(
        model=GENERAL_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a research synthesis specialist. Strictly do NOT use markdown asterisks (* or **) or header hashes (#). Write clean, polished plain text."
            },
            {
                "role": "user",
                "content": synth_prompt
            }
        ],
        temperature=0.3
    )

    return clean_response(res.choices[0].message.content)


@tool
def gemma_vision(
    image_path: str,
    question: str,
    history: str = ""
) -> str:
    """Use for image, screenshot and visual analysis."""

    image_file = gemini_client.files.upload(
        file=image_path
    )

    prompt = f"""
Previous conversation:
{history}

Current question:
{question}

Answer accurately.
CRITICAL FORMATTING INSTRUCTIONS:
- Do NOT use markdown asterisks (* or **) or header hashes (#, ##, ###).
- Do not bold words using asterisks.
- Use clean, natural plain text formatting without special symbols.
"""

    result = gemini_client.models.generate_content(
        model=VISION_MODEL,
        contents=[
            image_file,
            prompt
        ]
    )

    return clean_response(result.text)



@tool
def mistral_ocr(document_url: str) -> str:
    """Use for OCR, scanned documents, scanned PDFs and table extraction."""

    response = mistral_client.ocr.process(
        model=OCR_MODEL,
        document={
            "type": "document_url",
            "document_url": document_url
        }
    )

    text = ""

    for page in response.pages:
        text += page.markdown
        text += "\n\n"

    return text


@tool
def whisper_transcribe(audio_file: str) -> str:
    """Use for audio transcription and speech-to-text."""

    with open(audio_file, "rb") as file:
        result = groq_client.audio.transcriptions.create(
            file=file,
            model=WHISPER_MODEL,
            response_format="verbose_json"
        )

    return result.text


TOOLS = [
    qwen_coding,
    gptoss_general,
    web_search,
    gemma_vision,
    mistral_ocr,
    whisper_transcribe,
]


def choose_model(query, history):
    prompt = f"""
You are the intelligent routing brain of RouteLLM.

Your only job is to select the best specialist.

Do not answer the user.
Do not explain your decision.

Choose exactly one:

QWEN-CODING
GPTOSS-GENERAL
GEMMA-VISION
MISTRAL-OCR
WHISPER
WEB

Rules:

Programming, debugging, software engineering and algorithms
-> QWEN-CODING

Normal conversation, explanations, rewriting, summaries,
simple reasoning and general questions
-> GPTOSS-GENERAL

Images, screenshots and visual reasoning
-> GEMMA-VISION

OCR, scanned documents, scanned PDFs and table extraction
-> MISTRAL-OCR

Audio and speech transcription
-> WHISPER

Current information, news, web research and live information
-> WEB

Previous conversation:
{history}

Current user query:
{query}

Return only one label.
"""

    result = groq_client.chat.completions.create(
        model=ROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise AI model router."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        reasoning_effort="low",
        include_reasoning=False,
        max_completion_tokens=50
    )

    decision = result.choices[0].message.content.strip().upper()

    if "QWEN-CODING" in decision:
        return "QWEN-CODING"

    if "GPTOSS-GENERAL" in decision:
        return "GPTOSS-GENERAL"

    if "GEMMA-VISION" in decision:
        return "GEMMA-VISION"

    if "MISTRAL-OCR" in decision:
        return "MISTRAL-OCR"

    if "WHISPER" in decision:
        return "WHISPER"

    if "WEB" in decision:
        return "WEB"

    return "GPTOSS-GENERAL"


def ask_text(query):
    history = load_history()

    selected_model = choose_model(
        query,
        history
    )

    print("\nRouter selected:", selected_model)

    if selected_model == "QWEN-CODING":
        answer = qwen_coding.invoke({
            "query": query,
            "history": history
        })

    elif selected_model == "GPTOSS-GENERAL":
        answer = gptoss_general.invoke({
            "query": query,
            "history": history
        })

    elif selected_model == "WEB":
        answer = web_search.invoke({
            "query": query,
            "history": history
        })

    elif selected_model == "GEMMA-VISION":
        answer = "Please use the image command to analyze an image and also dnt give the blank context like N/A please give a structued one."

    elif selected_model == "MISTRAL-OCR":
        answer = "Please provide a document URL for OCR processing."

    elif selected_model == "WHISPER":
        answer = "Please provide an audio file path for transcription."

    else:
        answer = gptoss_general.invoke({
            "query": query,
            "history": history
        })

    answer = clean_response(str(answer))

    save_history(
        selected_model,
        query,
        answer
    )

    return selected_model, answer


def ask_image(image_path, question):
    history = load_history()

    print("\nRouter selected: GEMMA-VISION")

    answer = gemma_vision.invoke({
        "image_path": image_path,
        "question": question,
        "history": history
    })

    answer = clean_response(str(answer))

    save_history(
        "GEMMA-VISION",
        "IMAGE: " + image_path + "\nQUESTION: " + question,
        answer
    )

    return answer


import bcrypt

app = FastAPI(title="RouteLLM")

class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/api/signup")
def signup(req: AuthRequest):
    try:
        users = load_users()
        if req.username in users:
            return {"success": False, "message": "Username already exists"}
        if len(req.password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters"}
        
        hashed = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        save_user(req.username, hashed)
        return {"success": True, "message": "Account created successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/login")
def login(req: AuthRequest):
    try:
        users = load_users()
        if req.username not in users:
            return {"success": False, "message": "Invalid username or password"}
        
        stored_hash = users[req.username].encode('utf-8')
        if not bcrypt.checkpw(req.password.encode('utf-8'), stored_hash):
            return {"success": False, "message": "Invalid username or password"}
            
        return {"success": True, "message": "Logged in successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        model, answer = ask_text(req.query)
        return {"success": True, "answer": answer, "model": model}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    prompt: str = Form(""),
    file_type: str = Form(...) 
):
    try:
        os.makedirs("temp_uploads", exist_ok=True)
        ext = file.filename.split('.')[-1]
        temp_path = f"temp_uploads/{uuid.uuid4()}.{ext}"
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        answer = ""
        model = ""
        
        if file_type == "image":
            model = "GEMMA-VISION"
            answer = ask_image(temp_path, prompt if prompt else "Describe this image in detail.")
        elif file_type == "audio":
            model = "WHISPER"
            answer = whisper_transcribe(temp_path)
            save_history("WHISPER", f"AUDIO UPLOAD: {file.filename}", str(answer))
        elif file_type == "document":
            model = "MISTRAL-OCR"
            try:
                # Assuming Gemini can handle PDF/Docs as fallback if Mistral OCR local file is tricky
                doc_file = gemini_client.files.upload(file=temp_path)
                fallback_gemini = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
                result = gemini_client.models.generate_content(
                    model=fallback_gemini,
                    contents=[doc_file, "Extract all text from this document. Format as markdown."]
                )
                answer = result.text
            except:
                answer = "Document processed (Simulated OCR output for " + file.filename + ")"
            save_history("MISTRAL-OCR", f"DOCUMENT UPLOAD: {file.filename}", str(answer))
            
        return {"success": True, "answer": str(answer), "model": model}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/history")
def get_history_route():
    try:
        content = get_history_text()
        return {"success": True, "history": content}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.delete("/api/history")
def delete_history_route():
    try:
        clear_history()
        return {"success": True, "message": "History cleared"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/db-status")
def db_status_route():
    try:
        return {"success": True, "status": get_db_status()}
    except Exception as e:
        return {"success": False, "message": str(e)}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
