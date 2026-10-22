import os
import requests
from typing import Dict, Any, List, Optional
import openai  # O la librería correspondiente al cliente que prefieras usar

class LLMGateway:
    """
    Gateway agnóstico para enrutar peticiones de IA a diferentes proveedores 
    (OpenAI, Anthropic Claude, DeepSeek, Qwen, Kimi) o modelos locales.
    """
    
    @staticmethod
    def generar_respuesta(
        proveedor: str, 
        modelo: str, 
        mensajes: List[Dict[str, str]], 
        api_key: Optional[str] = None,
        temperatura: float = 0.7
    ) -> str:
        """
        Envía un prompt conversacional al LLM seleccionado de forma dinámica.
        """
        proveedor = proveedor.lower()
        
        if proveedor in ["openai", "gpt", "deepseek"]:
            # Configuración compatible con OpenAI / DeepSeek (OpenAI-like APIs)
            base_url = "https://api.deepseek.com/v1" if proveedor == "deepseek" else None
            client = openai.OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                base_url=base_url
            )
            
            response = client.chat.completions.create(
                model=modelo,
                messages=mensajes,
                temperature=temperatura
            )
            return response.choices[0].message.content

        elif proveedor == "anthropic" or proveedor == "claude":
            # Lógica para Anthropic Claude
            headers = {
                "x-api-key": api_key or os.getenv("ANTHROPIC_API_KEY"),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": modelo,
                "messages": mensajes,
                "max_tokens": 1024
            }
            response = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                raise Exception(f"Error en API de Claude: {response.text}")

        elif proveedor == "local":
            # Conexión a un modelo local (ej. Ollama desplegado en el servidor o Docker)
            local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/api/chat")
            payload = {
                "model": modelo,
                "messages": mensajes,
                "stream": False
            }
            response = requests.post(local_url, json=payload)
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "")
            else:
                raise Exception(f"Error conectando con modelo local: {response.text}")
                
        else:
            raise ValueError(f"Proveedor de LLM no soportado: {proveedor}")
