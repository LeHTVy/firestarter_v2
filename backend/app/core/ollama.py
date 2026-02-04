import httpx
import os
from typing import List, Dict, Any, Optional

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m['name'] for m in data.get('models', [])]
                return []
        except Exception:
            return []

    async def generate(self, model: str, prompt: str, system: Optional[str] = None):
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                if system:
                    payload["system"] = system
                    
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120.0
                )
                if response.status_code == 200:
                    return response.json()
                return {"error": f"Failed with status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False):
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": stream
                }
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=60.0
                )
                if response.status_code == 200:
                    return response.json()
                return {"error": "Failed to get response from Ollama"}
        except Exception as e:
            return {"error": str(e)}

ollama_client = OllamaClient()
