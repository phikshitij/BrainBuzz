import os
import requests
from typing import Optional

class OpenRouterAPI:
    def __init__(self, api_key: Optional[str] = None):
        # Try to get API key in this order: 1. provided key, 2. environment variable, 3. hardcoded key
        self.api_key = (
            api_key or 
            os.getenv("OPENROUTER_API_KEY") or
            "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"
        )
        
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. "
                "Please set the OPENROUTER_API_KEY environment variable or provide an API key."
            )
        
        # Clean and format the API key
        self.api_key = self.api_key.strip()
        self.api_key = self.api_key.strip('\'"')  # Remove any quotes
        
        # Ensure the API key has the correct prefix
        if not self.api_key.startswith('sk-'):
            self.api_key = f'sk-or-v1-{self.api_key}'
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Create a fresh headers dict to avoid any reference issues
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': 'http://localhost:8000',
            'X-Title': 'Piazza Learning Platform',
            'Content-Type': 'application/json'
        }
        
        # Debug: Print the first and last 4 chars of the API key to verify it's being set
        print("[DEBUG] API Key Configuration:")
        print(f"  - Raw API key from env: {os.getenv('OPENROUTER_API_KEY', 'Not found')}")
        print(f"  - Processed API key: {self.api_key[:8]}...{self.api_key[-4:] if len(self.api_key) > 8 else ''}")
        print("[DEBUG] Request Headers:")
        for k, v in self.headers.items():
            if k == 'Authorization':
                print(f"  {k}: {v[:8]}...{v[-4:] if len(v) > 8 else ''}")
            else:
                print(f"  {k}: {v}")
        print(f"[DEBUG] Base URL: {self.base_url}")
    
    def generate_response(self, message: str, model: str = "deepseek/deepseek-r1-0528-qwen3-8b:free") -> str:
        """
        Generate a response using OpenRouter's API with the specified model.
        
        Args:
            message (str): The user's message
            model (str): The model to use (default: deepseek/deepseek-r1-0528-qwen3-8b:free)
            
        Returns:
            str: The generated response or an error message
        """
        if not message or not isinstance(message, str):
            return "Error: Invalid message format. Please provide a valid string message."
        
        print(f"[DEBUG] Sending request to OpenRouter with model: {model}")
        headers_debug = {k: 'Bearer ***REDACTED***' if k == 'Authorization' else v for k, v in self.headers.items()}
        print(f"[DEBUG] Using headers: {headers_debug}")
            
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful teaching assistant for the Piazza learning platform."},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            print(f"[DEBUG] Request payload: {payload}")
            
            # Create a fresh set of headers
            request_headers = {
                'Authorization': f'Bearer {self.api_key}',  # Try with Bearer prefix
                'HTTP-Referer': 'http://localhost:8000',
                'X-Title': 'Piazza Learning Platform',
                'Content-Type': 'application/json'
            }
        
            print(f"[DEBUG] Sending request to: {self.base_url}")
            print(f"[DEBUG] Request headers: {request_headers}")
            print(f"[DEBUG] Request payload: {payload}")
            
            response = requests.post(
                self.base_url,
                headers=request_headers,
                json=payload,
                timeout=30
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"[DEBUG] Response data: {response_data}")
            except ValueError as e:
                print(f"[DEBUG] Failed to parse JSON response: {e}")
                print(f"[DEBUG] Raw response: {response.text}")
                return f"[Error] Invalid JSON response from API: {response.text}"
            
            if response.status_code != 200:
                error_msg = response_data.get("error", {})
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", str(error_msg))
                return f"[API Error {response.status_code}] {error_msg}"
                
            if not isinstance(response_data.get("choices"), list) or not response_data["choices"]:
                return "[Error] Invalid response format from the API. No choices available."
                
            return response_data["choices"][0].get("message", {}).get("content", "[Error] No content in response")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"[Network Error] Failed to connect to the API: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg
        except (KeyError, IndexError, TypeError) as e:
            error_msg = f"[Response Parsing Error] {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"[Unexpected Error] {type(e).__name__}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg

# Singleton instance
openrouter_client = OpenRouterAPI()

def get_openrouter_response(message: str) -> str:
    """Helper function to get a response from OpenRouter"""
    return openrouter_client.generate_response(message)
