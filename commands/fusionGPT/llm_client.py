import os, json, anthropic
from dotenv import load_dotenv
from ... import config
import traceback
from . import api_docs_retriever

# Load environment variables and get API key
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY") or config.ANTHROPIC_API_KEY 
if not api_key: raise ValueError("Anthropic API key not set")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=api_key)

# Initialize API documentation retriever
api_docs = api_docs_retriever.FusionAPIDocs()

# Base system message defining assistant behavior
BASE_SYSTEM_MESSAGE = """You are a Fusion 360 API expert. Generate executable Python code that creates 3D models using the Fusion 360 API.

You must follow these rules for EVERY Fusion 360 script:

1. ALWAYS place ALL code inside a run(context) function with thorough error handling:
```python
import adsk.core
import adsk.fusion
import traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        # Your code goes here
        
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\\n{}'.format(traceback.format_exc()))
```

2. ALWAYS initialize these core variables:
   - app = adsk.core.Application.get()
   - ui = app.userInterface
   - design = app.activeProduct
   - rootComp = design.rootComponent

3. Properly scope ALL variables, especially in event handlers.

4. Follow best practices:
   - Implement validation checks before performing operations
   - Use ValueInput correctly (createByReal for simple values, createByString for units)
   - Create descriptive variable names
   - Add clear comments
   - Break complex operations into simpler steps

5. NEVER generate code that would cause known API errors.

Remember, your code will be directly executed in Fusion 360. It must work reliably.
"""

def process_message(message, error_context=None):
    """
    Process user message using Anthropic Claude with RAG from API documentation
    
    Args:
        message (str): The user's message
        error_context (str, optional): Additional error context
        
    Returns:
        str: The response from Claude
    """
    try:
        # Retrieve relevant API documentation
        relevant_docs = api_docs.retrieve_relevant_docs(message)
        api_context = api_docs.format_as_context(relevant_docs)
        
        # If error context is provided, try to find solutions
        error_solution = None
        if error_context:
            error_solution = api_docs.retrieve_error_solution(error_context)
        
        # Create enhanced system message with RAG context
        enhanced_system_message = BASE_SYSTEM_MESSAGE
        
        if api_context:
            enhanced_system_message += "\n\n" + api_context
        
        if error_solution:
            enhanced_system_message += f"\n\nATTENTION - PREVIOUS ERROR TO FIX:\n{error_context}\n\nSOLUTION:\n{error_solution['solution']}\n"
        
        # Enhance the user message if it doesn't explicitly ask for code
        if any(keyword in message.lower() for keyword in ["create", "make", "generate", "model", "build", "design"]):
            enhanced_message = f"""
Create reliable Fusion 360 Python code that will accomplish this task:

{message}

IMPORTANT:
1. Your code must be COMPLETE and EXECUTABLE
2. Include VALIDATION CHECKS before each geometry operation
3. Use DEFENSIVE CODING to prevent errors
4. Follow ALL the API documentation guidance
5. Add helpful comments explaining your approach

The code WILL be directly executed in Fusion 360, so it must be robust.
"""
        else:
            enhanced_message = message
            
        # Call the API with explicit error handling
        try:
            response = client.messages.create(
                model="claude-3-7-sonnet-latest",
                system=enhanced_system_message,
                max_tokens=4000,
                messages=[{"role": "user", "content": enhanced_message}]
            )
            return response.content[0].text
        except Exception as api_error:
            error_details = f"API Error: {str(api_error)}\n{traceback.format_exc()}"
            return f"Error communicating with Claude: {error_details}"
            
    except Exception as e:
        error_details = f"Processing Error: {str(e)}\n{traceback.format_exc()}"
        return f"Error processing message: {error_details}"