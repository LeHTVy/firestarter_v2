from typing import List, Dict, Any
from app.core.ollama import ollama_client
from jinja2 import Environment, FileSystemLoader
import os

class PentestOrchestrator:
    def __init__(self):
        self.history = []
        # Setup Jinja2 environment
        # Points to backend/app/prompts
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    async def handle_request(self, user_prompt: str, model: str = "mistral"):
        # 1. Classification Step using Jinja2 template
        template = self.jinja_env.get_template("orchestrator.jinja2")
        system_prompt = template.render(user_prompt=user_prompt)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        response = await ollama_client.chat(model=model, messages=messages)
        content = response.get("message", {}).get("content", "I am standing by.")
        
        # Simple parsing for demonstration in UI
        if "[RESPONSE]" in content:
            display_content = content.split("[RESPONSE]")[-1].strip()
        else:
            display_content = content

        return display_content

orchestrator = PentestOrchestrator()
