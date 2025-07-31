# model.py

import google.genai as genai
from schemas import ChatRequest, FileData, Message as APIMessage
import dotenv
import os
from typing import Generator, List, Dict, Any, Union  
import base64
import PyPDF2
import docx
import io
import json
import csv
from pathlib import Path
from google.genai import types

dotenv.load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def process_image_for_gemini(file_data: FileData) -> Dict[str, Any]:
    """Process image for Gemini multimodal input using Part.from_bytes"""
    try:
        from google.genai import types
        
        # Decode base64 data
        image_bytes = base64.b64decode(file_data.data)
        
        # Create Part object for image
        return types.Part.from_bytes(
            data=image_bytes,
            mime_type=file_data.mime_type
        )
    except Exception as e:
        print(f"Error processing image {file_data.filename}: {e}")
        return None

def extract_pdf_content(file_data: FileData) -> str:
    """Extract text content from PDF file"""
    try:
        decoded_data = base64.b64decode(file_data.data)
        pdf_file = io.BytesIO(decoded_data)
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
            except Exception as e:
                text_content += f"\n--- Page {page_num} ---\n[Error extracting page content: {str(e)}]\n"
        
        if not text_content.strip():
            return "PDF file appears to be empty or contains only images/non-extractable content."
        
        return text_content.strip()
    
    except Exception as e:
        return f"Error extracting PDF content: {str(e)}"

def extract_docx_content(file_data: FileData) -> str:
    """Extract text content from DOCX file"""
    try:
        decoded_data = base64.b64decode(file_data.data)
        docx_file = io.BytesIO(decoded_data)
        
        doc = docx.Document(docx_file)
        text_content = ""
        
        # Extract paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content += paragraph.text + "\n"
        
        # Extract tables
        for table in doc.tables:
            text_content += "\n--- Table ---\n"
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    row_text.append(cell.text.strip())
                text_content += " | ".join(row_text) + "\n"
        
        if not text_content.strip():
            return "Word document appears to be empty."
        
        return text_content.strip()
    
    except Exception as e:
        return f"Error extracting Word document content: {str(e)}"

def extract_csv_content(file_data: FileData) -> str:
    """Extract and format CSV content"""
    try:
        decoded_data = base64.b64decode(file_data.data)
        csv_content = decoded_data.decode('utf-8')
        
        # Parse CSV
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.reader(csv_file)
        
        formatted_content = "CSV Data:\n"
        for row_num, row in enumerate(csv_reader, 1):
            if row_num == 1:
                formatted_content += "Headers: " + " | ".join(row) + "\n"
                formatted_content += "-" * 50 + "\n"
            else:
                formatted_content += f"Row {row_num-1}: " + " | ".join(row) + "\n"
            
            # Limit to first 100 rows for performance
            if row_num > 100:
                formatted_content += f"\n... (showing first 100 rows, total rows may be more)\n"
                break
        
        return formatted_content
    
    except Exception as e:
        return f"Error processing CSV: {str(e)}"

def extract_json_content(file_data: FileData) -> str:
    """Extract and format JSON content"""
    try:
        decoded_data = base64.b64decode(file_data.data)
        json_content = decoded_data.decode('utf-8')
        
        # Parse and pretty-print JSON
        json_data = json.loads(json_content)
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        return f"JSON Data:\n{formatted_json}"
    
    except json.JSONDecodeError as e:
        return f"Invalid JSON format: {str(e)}"
    except Exception as e:
        return f"Error processing JSON: {str(e)}"

def process_document_for_gemini(file_data: FileData) -> str:
    """Process document for text analysis with proper content extraction"""
    try:
        print(f"Processing document: {file_data.filename} (Type: {file_data.mime_type})")
        
        if file_data.mime_type == 'text/plain':
            decoded_data = base64.b64decode(file_data.data)
            content = decoded_data.decode('utf-8')
            return f"Text Document: {file_data.filename}\n\nContent:\n{content}"
        
        elif file_data.mime_type == 'text/csv':
            content = extract_csv_content(file_data)
            return f"CSV Document: {file_data.filename}\n\n{content}"
        
        elif file_data.mime_type == 'application/json':
            content = extract_json_content(file_data)
            return f"JSON Document: {file_data.filename}\n\n{content}"
        
        elif file_data.mime_type == 'application/pdf':
            content = extract_pdf_content(file_data)
            return f"PDF Document: {file_data.filename}\n\nExtracted Content:\n{content}"
        
        elif file_data.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            content = extract_docx_content(file_data)
            return f"Word Document: {file_data.filename}\n\nExtracted Content:\n{content}"
        
        elif file_data.mime_type == 'application/msword':
            return f"Legacy Word Document: {file_data.filename}\n\n[Legacy .doc format requires additional processing - please convert to .docx format for full analysis]"
        
        else:
            return f"Document: {file_data.filename} (Type: {file_data.mime_type})\n[Unsupported document type for content extraction]"
    
    except Exception as e:
        print(f"Error processing document {file_data.filename}: {e}")
        return f"Error processing document {file_data.filename}: {str(e)}"

def process_file_for_gemini(file_data: FileData) -> Union[Dict[str, Any], str]:
    """Process file for Gemini - returns image part or document text"""
    if file_data.mime_type.startswith('image/'):
        return process_image_for_gemini(file_data)
    else:
        return process_document_for_gemini(file_data)

def build_conversation_contents(history: List[APIMessage], current_message: ChatRequest) -> List[Dict[str, Any]]:
    """Build conversation contents for Gemini API in correct format"""
    contents = []
    
    # Add conversation history
    for msg in history:
        if msg.role == 'user':
            parts = []
            
            # Add text content
            if msg.content:
                parts.append({"text": msg.content})
            
            # Add files if any
            if hasattr(msg, 'files') and msg.files:
                for file_data in msg.files:
                    processed_file = process_file_for_gemini(file_data)
                    
                    if file_data.mime_type.startswith('image/') and processed_file:
                        # Add image part directly
                        parts.append(processed_file)
                    elif isinstance(processed_file, str):
                        # Add document content as text
                        parts.append({"text": processed_file})
            
            if parts:  # Only add if there are parts
                contents.append({
                    "role": "user",
                    "parts": parts
                })
        
        elif msg.role == 'assistant':
            contents.append({
                "role": "model",
                "parts": [{"text": msg.content}]
            })
    
    # Add current message
    current_parts = []
    
    # Add text content
    if current_message.message.text:
        current_parts.append({"text": current_message.message.text})
    
    # Process attached files
    for file_data in current_message.message.files:
        processed_file = process_file_for_gemini(file_data)
        
        if file_data.mime_type.startswith('image/') and processed_file:
            # Vision processing
            current_parts.append(processed_file)
            print(f"Added image for vision analysis: {file_data.filename}")
        elif isinstance(processed_file, str):
            # Document analysis
            current_parts.append({"text": processed_file})
            print(f"Added document for analysis: {file_data.filename}")
    
    # Add current message to conversation
    if current_parts:  # Only add if there are parts
        contents.append({
            "role": "user",
            "parts": current_parts
        })
    
    return contents

def my_genai_chat_function_stream(payload: ChatRequest) -> Generator[str, None, None]:
    """
    Enhanced streaming function with proper document analysis
    """
    if not payload.message.text and not payload.message.files:
        yield "No message content provided."
        return
    
    try:
        print(f"Processing message: {payload.message.text}")
        print(f"Using model: {payload.model_name}")
        print(f"Files attached: {len(payload.message.files)}")
        print(f"History length: {len(payload.history)}")
        
        # Build conversation contents in correct format
        contents = build_conversation_contents(payload.history, payload)
        
        if not contents:
            yield "No valid content to process."
            return
        
        print("Starting stream response...")
        print(f"Contents structure: {len(contents)} messages")
        
        # Enhanced system instruction for document analysis
        system_instruction = """You are an AI assistant with advanced document analysis and vision capabilities. 
When analyzing documents:
- Provide detailed summaries and insights
- Extract key information, data, and patterns
- Answer questions about document content accurately
- For images, describe what you see in detail
- For data files (CSV, JSON), provide statistical insights when relevant
- Always be thorough but concise in your analysis"""
        
        # Use proper SDK method with system instruction
        response = client.models.generate_content_stream(
            model=payload.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=8192
            )
        )
        
        # Stream the response
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text
        
        print("Stream response completed")
    
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        yield f"Error generating response: {str(e)}"

def my_genai_chat_function(payload: ChatRequest) -> str:
    """
    Non-streaming version with enhanced document analysis
    """
    if not payload.message.text and not payload.message.files:
        return "No message content provided."
    
    try:
        # Build conversation contents
        contents = build_conversation_contents(payload.history, payload)
        
        if not contents:
            return "No valid content to process."
        
        # Enhanced system instruction for document analysis
        system_instruction = """You are an AI assistant with advanced document analysis and vision capabilities. 
When analyzing documents:
- Provide detailed summaries and insights
- Extract key information, data, and patterns
- Answer questions about document content accurately
- For images, describe what you see in detail
- For data files (CSV, JSON), provide statistical insights when relevant
- Always be thorough but concise in your analysis"""
        
        # Use proper SDK method with system instruction
        response = client.models.generate_content(
            model=payload.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=8192
            )
        )
        
        if response and hasattr(response, 'text') and response.text:
            return response.text
        else:
            return "No response from model."
    
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return f"Error generating response: {str(e)}"
