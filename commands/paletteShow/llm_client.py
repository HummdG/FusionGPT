import os, json, anthropic
from dotenv import load_dotenv
from ... import config

# Load environment variables and get API key
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY") or config.ANTHROPIC_API_KEY 
if not api_key: raise ValueError("Anthropic API key not set")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=api_key)



# System message defining assistant behavior
system_message = """You are a Fusion 360 API expert. Generate executable Python code using only standard Fusion 360 API (adsk.core, adsk.fusion). Include proper error handling with correct variable scoping. Format code with ```python tags."""



def process_message(message):
    """Process user message using Anthropic Claude"""
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            system=system_message,
            max_tokens=4000,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error communicating with Claude: {str(e)}"