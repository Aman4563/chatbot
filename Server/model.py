from __future__ import annotations

import base64
import csv
import io
import json
import os
import re
from typing import Any, Dict, Generator, List, Optional, Tuple

import dotenv
import docx
import PyPDF2
from huggingface_hub import InferenceClient

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI

from schemas import ChatRequest, FileData, Message as APIMessage

dotenv.load_dotenv()

# ==============================
# Environment configuration
# ==============================
ENV_KEYS = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "HUGGINGFACE_API_KEY": os.getenv("HUGGINGFACE_API_KEY"),
}

def _get_env_flag(name: str, default: str) -> str:
    """Get environment variable as lowercase flag."""
    value = os.getenv(name)
    return value.strip().lower() if isinstance(value, str) and value.strip() else default

def _get_env_int(name: str, default: int) -> int:
    """Get environment variable as integer with fallback."""
    try:
        return int(os.getenv(name, "").strip())
    except (ValueError, AttributeError):
        return default

# Gemini tool configuration
GEMINI_TOOL_DEFAULT = _get_env_flag("GEMINI_TOOL_DEFAULT", "auto")
GEMINI_TOOL_MAX_QUERIES = _get_env_int("GEMINI_TOOL_MAX_QUERIES", 2)
GEMINI_TOOL_DISABLE_FOR_CS = _get_env_flag("GEMINI_TOOL_DISABLE_FOR_CS", "1") in {"1", "true", "yes"}
GEMINI_IMAGE_TOOL_DEFAULT = _get_env_flag("GEMINI_IMAGE_TOOL_DEFAULT", "never")

# ==============================
# Model configuration helpers
# ==============================
def _create_model_config(provider: str, model_class, model_name: str, 
                        supports_vision: bool = True, supports_files: bool = True) -> Dict[str, Any]:
    """Create standardized model configuration."""
    return {
        "provider": provider,
        "class": model_class,
        "model": model_name,
        "supports_vision": supports_vision,
        "supports_files": supports_files,
        "api_key": ENV_KEYS[f"{provider.upper()}_API_KEY"],
    }

# ==============================
# Model configuration (providers)
# ==============================
MODEL_CONFIG: Dict[str, Dict[str, Any]] = {
    # Mistral models
    "mistral-large": _create_model_config("mistral", ChatMistralAI, "mistral-large-latest", False),
    "mistral-small": _create_model_config("mistral", ChatMistralAI, "mistral-small-latest", False),
    
    # OpenAI models
    "gpt-4o": _create_model_config("openai", ChatOpenAI, "gpt-4o"),
    "gpt-4o-mini": _create_model_config("openai", ChatOpenAI, "gpt-4o-mini"),
    
    # Anthropic models
    "claude-3-5-sonnet": _create_model_config("anthropic", ChatAnthropic, "claude-3-5-sonnet-20241022"),
    
    # Google Gemini models
    "gemini-1.5-pro": _create_model_config("google", ChatGoogleGenerativeAI, "gemini-1.5-pro"),
    "gemini-1.5-flash": _create_model_config("google", ChatGoogleGenerativeAI, "gemini-1.5-flash"),
    "gemini-2.0-flash": _create_model_config("google", ChatGoogleGenerativeAI, "gemini-2.0-flash"),
    "gemini-2.5-flash": _create_model_config("google", ChatGoogleGenerativeAI, "gemini-2.5-flash"),
    "gemini-2.5-pro": _create_model_config("google", ChatGoogleGenerativeAI, "gemini-2.5-pro"),
}

# ================
# Optional legacy web tool (not used by Gemini; kept for completeness)
# ================
def web_search_tool(query: str, num_results: int = 5) -> List[str]:
    try:
        from googlesearch import search
    except ImportError as e:
        raise RuntimeError("Missing dependency: pip install googlesearch-python") from e
    results: List[str] = []
    for url in search(query):
        if not url.lower().startswith(("http://", "https://")):
            continue
        results.append(url)
        if len(results) >= num_results:
            break
    return results

# ==========================
# File & content processing
# ==========================
def process_image_for_langchain(file_data: FileData) -> Optional[Dict[str, Any]]:
    """Prepare an image attachment for multimodal models that accept image_url."""
    try:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{file_data.mime_type};base64,{file_data.data}"},
        }
    except Exception as e:
        print(f"Error processing image {file_data.filename}: {e}")
        return None

# Content extraction registry
CONTENT_EXTRACTORS = {
    "application/pdf": lambda data: _extract_pdf_content(data),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": lambda data: _extract_docx_content(data),
    "text/csv": lambda data: _extract_csv_content(data),
    "application/json": lambda data: _extract_json_content(data),
    "text/plain": lambda data: base64.b64decode(data).decode("utf-8"),
}

def _extract_pdf_content(data: str) -> str:
    """Extract text content from a PDF."""
    try:
        decoded = base64.b64decode(data)
        reader = PyPDF2.PdfReader(io.BytesIO(decoded))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"--- Page {i} ---\n{text}")
            except Exception as e:
                pages.append(f"[Error extracting page {i}: {e}]")
        return "\n".join(pages) if pages else "PDF appears empty or image-only."
    except Exception as e:
        return f"Error extracting PDF: {e}"

def _extract_docx_content(data: str) -> str:
    """Extract text content from a DOCX file."""
    try:
        decoded = base64.b64decode(data)
        document = docx.Document(io.BytesIO(decoded))
        parts = [p.text for p in document.paragraphs if p.text.strip()]
        
        # Add table content
        for table in document.tables:
            parts.append("\n--- Table ---")
            parts.extend(" | ".join(cell.text.strip() for cell in row.cells) for row in table.rows)
        
        return "\n".join(parts) if parts else "Word document appears to be empty."
    except Exception as e:
        return f"Error extracting Word document content: {e}"

def _extract_csv_content(data: str) -> str:
    """Extract and format CSV content (first 100 rows)."""
    try:
        decoded = base64.b64decode(data).decode("utf-8")
        csv_reader = csv.reader(io.StringIO(decoded))
        lines = ["CSV Data:"]
        
        for idx, row in enumerate(csv_reader, 1):
            if idx == 1:
                lines.extend(["Headers: " + " | ".join(row), "-" * 50])
            else:
                lines.append(f"Row {idx - 1}: " + " | ".join(row))
            if idx >= 100:
                lines.append("... (showing first 100 rows)")
                break
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error processing CSV: {e}"

def _extract_json_content(data: str) -> str:
    """Pretty-print JSON content."""
    try:
        decoded = base64.b64decode(data).decode("utf-8")
        obj = json.loads(decoded)
        return "JSON Data:\n" + json.dumps(obj, indent=2, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
    except Exception as e:
        return f"Error processing JSON: {e}"

def process_document_for_langchain(file_data: FileData) -> str:
    """Route to the appropriate extractor for supported document types."""
    try:
        # Handle legacy Word documents
        if file_data.mime_type == "application/msword":
            return (f"Legacy Word Document: {file_data.filename}\n\n"
                   "[Legacy .doc requires conversion to .docx for full analysis]")
        
        # Use extractor registry
        extractor = CONTENT_EXTRACTORS.get(file_data.mime_type)
        if extractor:
            content = extractor(file_data.data)
            doc_type = file_data.mime_type.split('/')[-1].upper()
            return f"{doc_type} Document: {file_data.filename}\n\n{content}"
        
        return f"Document: {file_data.filename} (Type: {file_data.mime_type})\n[Unsupported type]"
    except Exception as e:
        return f"Error processing document {file_data.filename}: {e}"

# ======================
# Conversation assembly
# ======================
def _process_message_files(files: List[FileData]) -> List[Dict[str, Any]]:
    """Process files for a message into content parts."""
    parts = []
    for f in files:
        if f.mime_type.startswith("image/"):
            img = process_image_for_langchain(f)
            if img:
                parts.append(img)
        else:
            parts.append({"type": "text", "text": process_document_for_langchain(f)})
    return parts

def _create_message_content(text: Optional[str], files: List[FileData]) -> List[Dict[str, Any]]:
    """Create content parts for a message."""
    parts = []
    if text:
        parts.append({"type": "text", "text": text})
    parts.extend(_process_message_files(files))
    return parts

def _format_langchain_message(content_parts: List[Dict[str, Any]], is_user: bool):
    """Format content parts into appropriate LangChain message."""
    if not content_parts:
        return None
    
    if len(content_parts) == 1 and content_parts[0].get("type") == "text":
        content = content_parts[0]["text"]
    else:
        content = content_parts
    
    return HumanMessage(content=content) if is_user else AIMessage(content=content)

def build_conversation_messages(
    history: List[APIMessage], current: ChatRequest, system_prompt: Optional[str]
) -> List:
    """Compose messages for LangChain models, including multimodal content."""
    msgs = []
    if system_prompt:
        msgs.append(SystemMessage(content=system_prompt))

    # Process history
    for msg in history:
        if msg.role == "user":
            content_parts = _create_message_content(msg.content, getattr(msg, "files", []))
            message = _format_langchain_message(content_parts, is_user=True)
            if message:
                msgs.append(message)
        elif msg.role == "assistant":
            msgs.append(AIMessage(content=msg.content))

    # Process current message
    current_parts = _create_message_content(current.message.text, current.message.files)
    current_message = _format_langchain_message(current_parts, is_user=True)
    if current_message:
        msgs.append(current_message)
    
    return msgs

# ===========================
# Gemini tool policy & control
# ===========================
_FORCE_SEARCH_TERMS = (
    "search online", "google it", "google this", "check the web",
    "web search", "browse the web", "look it up", "lookup online", "check online"
)

_CS_SEARCH_NEG = (
    "binary search", "search tree", "graph search", "search algorithm",
    "search complexity", "dfs", "bfs"
)

_FORCE_IMAGE_TERMS = (
    "generate an image", "generate image", "create an image", "make an image",
    "draw", "illustration", "diagram", "sketch", "logo", "wallpaper",
    "poster", "render", "picture of", "image of", "make a picture"
)

def _should_block_for_cs(prompt: str) -> bool:
    p = (prompt or "").lower()
    return GEMINI_TOOL_DISABLE_FOR_CS and any(kw in p for kw in _CS_SEARCH_NEG)

def _is_forced_search(prompt: str) -> bool:
    p = (prompt or "").lower()
    return any(kw in p for kw in _FORCE_SEARCH_TERMS)

def _is_forced_image(prompt: str) -> bool:
    p = (prompt or "").lower()
    return any(kw in p for kw in _FORCE_IMAGE_TERMS)

def _is_gemini_model(model_name: str) -> bool:
    return (model_name or "").startswith("gemini")

def _gemini_policy_text(max_queries: int, enable_image_json: bool) -> str:
    base = (
        "You can use web search (Google Search tool) ONLY if the answer depends on current or external information "
        "such as recent news, live results, release dates, prices, schedules, weather, or fast-changing facts. "
        f"Be frugal: perform at most {max_queries} searches unless absolutely necessary. "
        "If the query is answerable from your internal knowledge, do not use the tool. "
        "When you do use the tool, prefer a small number of targeted searches."
    )
    if enable_image_json:
        base += (
            "\nIf creating an image would satisfy the user's request or significantly help, "
            "emit a single-line JSON directive as the VERY FIRST LINE of your reply, like:\n"
            '{"tool":"generate_image","prompt":"<clear descriptive prompt>","model":"<optional hf model id>"}\n'
            "After that JSON line, continue with your normal answer."
        )
    return base

def get_gemini_tools_and_policy(model_name: str, prompt: str) -> Tuple[List[Any], Optional[str], bool]:
    """
    Build the Gemini tools list (only google_search to avoid function_declarations) and a policy message.
    Returns (tools, policy_text, image_json_enabled).
    image_json_enabled=True means we asked the model to optionally emit the image JSON directive.
    """
    if not _is_gemini_model(model_name):
        return [], None, False

    tools: List[Any] = []
    image_json_enabled = False

    # GOOGLE SEARCH TOOL (dict shape for wrapper compatibility)
    if GEMINI_TOOL_DEFAULT != "never" and not _should_block_for_cs(prompt):
        if _is_forced_search(prompt) or GEMINI_TOOL_DEFAULT in {"auto", "always"}:
            tools.append({"google_search": {}})

    # IMAGE directive (no function_declarations — we parse JSON ourselves)
    # Only enable when explicitly requested to maintain streaming performance
    if GEMINI_IMAGE_TOOL_DEFAULT == "always" or _is_forced_image(prompt):
        image_json_enabled = True

    policy = _gemini_policy_text(GEMINI_TOOL_MAX_QUERIES, enable_image_json=image_json_enabled)
    return tools, policy, image_json_enabled

def _insert_policy_message(messages: List, policy: Optional[str]) -> List:
    if not policy:
        return messages
    idx = 0
    if messages and isinstance(messages[0], SystemMessage):
        idx = 1
    return messages[:idx] + [SystemMessage(content=policy)] + messages[idx:]

# =============================
# Model initialization helpers
# =============================
def get_model(model_name: str):
    """Initialize and return the appropriate LangChain chat model."""
    if model_name not in MODEL_CONFIG:
        raise ValueError(f"Unsupported model: {model_name}")

    cfg = MODEL_CONFIG[model_name]
    api_key = cfg["api_key"]
    if not api_key:
        raise ValueError(f"API key not found for {cfg['provider']} models")

    provider = cfg["provider"]
    model_cls = cfg["class"]

    # Enhanced Google/Gemini configuration for better streaming
    if provider == "google":
        return model_cls(
            model=cfg["model"],
            google_api_key=api_key,
            max_output_tokens=8192,
            temperature=0.7,
            # Enable streaming support for better real-time responses
            streaming=True,
        )
    else:
        return model_cls(
            model=cfg["model"],
            api_key=api_key,
            max_tokens=8192,
            temperature=0.7,
        )

# ===================
# Image generation
# ===================
def image_gen_tool(prompt: str, model_id: Optional[str] = None, local_image_path: Optional[str] = None) -> str:
    """
    Image URL provider with multiple modes.
    
    Modes (set with env IMAGE_GEN_MODE):
      - local (default): read a local PNG and return data URL
      - hf: Hugging Face generation (when implemented)
      - placeholder: return a static placeholder URL
    """
    mode = os.getenv("IMAGE_GEN_MODE", "local").strip().lower()
    placeholder_url = "https://picsum.photos/1024"

    if mode == "local":
        path = local_image_path or os.getenv("IMAGE_GEN_LOCAL_PATH", "generated_image.png")
        try:
            with open(path, "rb") as f:
                img_bytes = f.read()
            # Debug copy
            with open("debug_local_image_copy.png", "wb") as dbg:
                dbg.write(img_bytes)
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except (FileNotFoundError, Exception) as e:
            print(f"[image_gen_tool] Local image error: {e}. Using placeholder.")
            return placeholder_url

    elif mode == "hf":
        hf_token = ENV_KEYS.get("HUGGINGFACE_API_KEY")
        if not hf_token:
            print("[image_gen_tool] No HUGGINGFACE_API_KEY; using placeholder.")
            return placeholder_url

        try:
            # TODO: Implement HF generation when needed
            # client = InferenceClient(api_key=hf_token)
            # model_to_use = model_id or os.getenv("HF_TTI_MODEL", "black-forest-labs/FLUX.1-schnell")
            # image = client.text_to_image(prompt, model=model_to_use)
            # ... conversion logic ...
            raise RuntimeError("HF generation not implemented yet")
        except Exception as e:
            print(f"[image_gen_tool] HF generation failed: {e}. Using placeholder.")
            return placeholder_url

    # Fallback mode
    return placeholder_url




# ===================
# Invocation helpers
# ===================
def _invoke_with_optional_tools(model, messages, tools):
    try:
        if tools:
            return model.invoke(messages, tools=tools)
        return model.invoke(messages)
    except TypeError:
        if tools:
            try:
                return model.invoke(messages, tool_config={"tools": tools})
            except TypeError:
                pass
        return model.invoke(messages)

def _stream_with_optional_tools(model, messages, tools):
    try:
        if tools:
            return model.stream(messages, tools=tools)
        return model.stream(messages)
    except TypeError:
        if tools:
            try:
                return model.stream(messages, tool_config={"tools": tools})
            except TypeError:
                pass
        return model.stream(messages)

_JSON_LINE_RE = re.compile(r'^\s*\{.*\}\s*$', re.DOTALL)

def _maybe_parse_tool_json(first_line: str) -> Optional[Dict[str, Any]]:
    try:
        obj = json.loads(first_line.strip())
        if isinstance(obj, dict) and obj.get("tool") == "generate_image":
            return obj
    except Exception:
        pass
    return None

def _extract_first_line(text: str) -> str:
    # Handle codefence or plain first line
    t = text.strip()
    if t.startswith("```"):
        # try to pull first JSON object inside fence
        # Simple heuristic: grab first non-empty line inside
        lines = [ln for ln in t.splitlines() if ln.strip()]
        if len(lines) >= 2 and lines[1].startswith("{"):
            return lines[1]
    # otherwise just first line
    return t.splitlines()[0] if "\n" in t else t

# ===================
# Public inference APIs
# ===================
def my_genai_chat_function_stream(payload: ChatRequest) -> Generator[str, None, None]:
    """
    Enhanced streaming chat generation with improved Gemini support.
    Properly streams responses while supporting image generation when explicitly requested.
    """
    if not payload.message.text and not payload.message.files:
        yield "No message content provided."
        return
        
    try:
        print(f"🚀 Starting streaming for model: {payload.model_name}")
        model = get_model(payload.model_name)
        messages = build_conversation_messages(payload.history, payload, payload.system_prompt)
        
        if not messages:
            yield "No valid content to process."
            return

        tools, policy, image_json_enabled = get_gemini_tools_and_policy(
            payload.model_name, payload.message.text or ""
        )
        print(f"📊 Gemini config: tools={len(tools)}, policy_enabled={bool(policy)}, "
              f"image_json_enabled={image_json_enabled}")
        
        if policy:
            messages = _insert_policy_message(messages, policy)

        # Enhanced streaming for image JSON directives
        if image_json_enabled:
            yield from _handle_image_json_streaming(model, messages, tools)
            return

        # Normal streaming (no image directive expected)
        print("⚡ Using normal streaming mode")
        yield from _handle_normal_streaming(model, messages, tools)
        
    except Exception as e:
        print(f"Error in LangChain stream call: {e}")
        yield f"Error generating response: {e}"


def _handle_image_json_streaming(model, messages, tools):
    """Handle streaming with image JSON directive detection."""
    print("🖼️  Image JSON enabled - using enhanced streaming with directive detection")
    
    first_chunk_received = False
    accumulated_content = ""
    
    for chunk in _stream_with_optional_tools(model, messages, tools):
        if not getattr(chunk, "content", None):
            continue
            
        chunk_content = chunk.content
        if isinstance(chunk_content, list):
            chunk_content = " ".join(str(p) for p in chunk_content if p)
        
        if not first_chunk_received:
            first_chunk_received = True
            accumulated_content = chunk_content
            
            # Check for JSON directive
            first_line = _extract_first_line(accumulated_content)
            tool_req = _maybe_parse_tool_json(first_line)
            
            if tool_req:
                # Generate and yield image
                img_url = image_gen_tool(tool_req.get("prompt", ""), tool_req.get("model"))
                yield f"![generated]({img_url})\n\n"
                
                # Send remaining content (minus JSON line)
                remaining_first = "\n".join(accumulated_content.splitlines()[1:]).strip()
                if remaining_first:
                    yield remaining_first
            else:
                yield chunk_content
        else:
            yield chunk_content
    
    if not first_chunk_received:
        yield "No response from model."


def _handle_normal_streaming(model, messages, tools):
    """Handle normal streaming without special processing."""
    for chunk in _stream_with_optional_tools(model, messages, tools):
        if getattr(chunk, "content", None):
            if isinstance(chunk.content, list):
                yield " ".join(str(p) for p in chunk.content if p)
            else:
                yield chunk.content

def my_genai_chat_function(payload: ChatRequest) -> str:
    """Non-streaming variant—Gemini decides search tool; image-gen via JSON directive on first line."""
    if not payload.message.text and not payload.message.files:
        return "No message content provided."
    try:
        model = get_model(payload.model_name)
        messages = build_conversation_messages(payload.history, payload, payload.system_prompt)
        if not messages:
            return "No valid content to process."

        tools, policy, image_json_enabled = get_gemini_tools_and_policy(payload.model_name, payload.message.text or "")
        if policy:
            messages = _insert_policy_message(messages, policy)

        resp = _invoke_with_optional_tools(model, messages, tools)
        content = getattr(resp, "content", "") or ""
        if isinstance(content, list):
            content = " ".join(str(p) for p in content if p)

        if image_json_enabled and content:
            first = _extract_first_line(content)
            tool_req = _maybe_parse_tool_json(first)
            if tool_req:
                img_url = image_gen_tool(tool_req.get("prompt", ""), tool_req.get("model"))
                remaining = "\n".join(content.splitlines()[1:]).strip()
                final = f"![generated]({img_url})\n\n{remaining or ''}".strip()
                return final or "No response from model."

        return content or "No response from model."
    except Exception as e:
        print(f"Error in LangChain call: {e}")
        return f"Error generating response: {e}"