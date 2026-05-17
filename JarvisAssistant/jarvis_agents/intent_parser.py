import requests
import json
from jarvis_core.config import config

class IntentParser:
    def __init__(self):
        self.url = config.OLLAMA_URL
        self.model = config.OLLAMA_MODEL
        
        self.system_prompt = """
        You are JARVIS, a highly advanced multi-device AI assistant.
        Your job is to parse the user's natural language command into a structured JSON format.
        Available devices: "laptop", "phone", "tablet". (If not specified, assume "laptop").
        Available actions: "open_app", "send_message", "search_web", "system_control", "chat".
        
        Output ONLY valid JSON.
        Format:
        {
            "action": "open_app" | "send_message" | "search_web" | "system_control" | "chat",
            "target_device": "laptop" | "phone" | "tablet",
            "parameters": {
                "app_name": "whatsapp/youtube/etc",
                "message": "text if applicable",
                "contact_name": "recipient name for messaging",
                "channel": "whatsapp/sms/email/etc",
                "operation": "open_app|close_app|type_text|hotkey|clipboard_copy|clipboard_paste",
                "keys": ["ctrl","shift","s"],
                "text": "text to type for system control",
                "query": "search query if applicable",
                "response_text": "What JARVIS should say back to the user (e.g. 'Opening WhatsApp on your phone', 'I have turned off the lights')"
            }
        }
        Rules:
        - If the user asks to send a WhatsApp message, use action="send_message", parameters.channel="whatsapp", and fill contact_name + message.
        - If user says "tell Rahul I reached home", infer send_message to whatsapp unless another channel is explicit.
        - For close app / keyboard actions, use action="system_control" with parameters.operation and other fields.
        """

    def parse_intent(self, user_text: str) -> dict:
        prompt = f"User Command: '{user_text}'\nParse this into JSON."
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": self.system_prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            data = response.json()
            intent_json = json.loads(data['response'])
            return intent_json
        except Exception as e:
            print(f"Error parsing intent with Ollama: {e}")
            return {
                "action": "chat",
                "target_device": "laptop",
                "parameters": {
                    "response_text": "I encountered an error while processing your request."
                }
            }

if __name__ == "__main__":
    parser = IntentParser()
    print(parser.parse_intent("Jarvis, open YouTube on my tablet"))
