import os
from typing import Any, Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Try the new SDK first; fall back to the old one if not installed.
USING_NEW = True
try:
    from google import genai as genai_new
    from google.genai import types as genai_types  # new SDK types
except Exception:
    USING_NEW = False
    import google.generativeai as genai_old  # old SDK

def _guess_mime(path: str) -> str:
    p = path.lower()
    if p.endswith(".png"): return "image/png"
    if p.endswith(".webp"): return "image/webp"
    if p.endswith(".gif"): return "image/gif"
    return "image/jpeg"

class GeminiVisionInput(BaseModel):
    images: str | List[str] = Field(
        description="Path(s) or URL(s) to the image(s) to analyze. Can be a single string or a list."
    )

class CustomGeminiVisionTool(BaseTool):
    name: str = "Gemini Vision Analyzer"
    description: str = (
        "Analyzes one or more images using Gemini's vision capabilities to extract visual details "
        "such as landmarks, architecture, scenery, or other identifiable features for location identification."
    )
    args_schema: Type[BaseModel] = GeminiVisionInput

    def _run(self, images: str | List[str]) -> str:
        # Accept both GOOGLE_API_KEY (new SDK default) and GEMINI_API_KEY (your current env)
        api_key = os.getenv("GEMINI_API_KEY")
        print(api_key)
        if not api_key:
            raise ValueError("Set GOOGLE_API_KEY (preferred) or GEMINI_API_KEY in your environment.")

        # Normalize images -> list
        if isinstance(images, str):
            images = [images]

        # Build prompt
        prompt = (
            "Extract key visual features from these images that could help identify the location. "
            "Describe landmarks, buildings, natural features, text, or unique elements in detail."
        )

        # Prepare parts and call the right SDK
        if USING_NEW:
            # New Google Gen AI SDK (google-genai)
            # https://googleapis.github.io/python-genai/  | client + types.Part
            client = genai_new.Client(api_key=api_key)
            parts = [genai_types.Part.from_text(text=prompt)]
            for path in images:
                if path.startswith(("http://", "https://")):
                    # Minimal URL handling: download to bytes (avoid extra deps)
                    import urllib.request
                    with urllib.request.urlopen(path) as resp:
                        data = resp.read()
                    mime = resp.headers.get_content_type() or "image/jpeg"
                else:
                    if not os.path.exists(path):
                        raise ValueError(f"Image not found: {path}")
                    with open(path, "rb") as f:
                        data = f.read()
                    mime = _guess_mime(path)

                parts.append(genai_types.Part.from_bytes(data=data, mime_type=mime))

            resp = client.models.generate_content(
                model="gemini-1.5-flash",  # fast, vision-capable
                contents=parts,
            )
            if hasattr(resp, "text") and resp.text:
                return resp.text
            raise ValueError("Gemini response was empty.")

        else:
            # Old SDK (google-generativeai) — now deprecated but still widely used
            # https://ai.google.dev/gemini-api/docs/migrate  | https://pypi.org/project/google-generativeai/
            genai_old.configure(api_key=api_key)
            model = genai_old.GenerativeModel("gemini-1.5-flash")
            image_parts = []
            for path in images:
                if path.startswith(("http://", "https://")):
                    import urllib.request
                    with urllib.request.urlopen(path) as resp:
                        data = resp.read()
                    mime = resp.headers.get_content_type() or "image/jpeg"
                else:
                    if not os.path.exists(path):
                        raise ValueError(f"Image not found: {path}")
                    with open(path, "rb") as f:
                        data = f.read()
                    mime = _guess_mime(path)

                # Old SDK accepts inline dicts with mime/data
                image_parts.append({"mime_type": mime, "data": data})

            resp = model.generate_content([prompt, *image_parts])
            if hasattr(resp, "text") and resp.text:
                return resp.text
            raise ValueError("Gemini response was empty.")

    def _arun(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Async operation not supported yet.")
