import os, json, anthropic
from dotenv import load_dotenv
from ... import config
import traceback

# Load environment variables and get API key
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY") or config.ANTHROPIC_API_KEY 
if not api_key: raise ValueError("Anthropic API key not set")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=api_key)

# System message defining assistant behavior
system_message = """You are a Fusion 360 API expert. Generate executable Python code that creates 3D models using the Fusion 360 API.

IMPORTANT: All code you provide MUST be executable directly within Fusion 360.

Follow these rules when writing Fusion 360 code:

1. Always place ALL code inside a run(context) function like this:
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
        
    except:
        if ui:
            ui.messageBox('Failed:\\n{}'.format(traceback.format_exc()))
```

2. ALWAYS use proper error handling with try/except blocks around ALL code.

3. ALWAYS initialize these variables in EVERY script:
   - app = adsk.core.Application.get()
   - ui = app.userInterface
   - design = app.activeProduct
   - rootComp = design.rootComponent

4. Properly scope variables. Variables defined inside event handlers must be accessed as nonlocal or global.

5. For object creation (sketches, extrudes, etc.), follow this approach:
   - Get the container: sketches = rootComp.sketches
   - Create the object: sketch = sketches.add(plane)
   - Get features: extrudes = rootComp.features.extrudeFeatures
   - Create inputs: input = extrudes.createInput(...)
   - Set properties: input.setDistanceExtent(...)
   - Create the feature: extrude = extrudes.add(input)

6. When creating points, use: adsk.core.Point3D.create(x, y, z)

7. When specifying dimensions, use ValueInput: adsk.core.ValueInput.createByReal(5) or adsk.core.ValueInput.createByString('5 mm')

8. ALWAYS use the complete code structure - all imported modules, function definitions, error handling, and actual code implementation.

Remember, your code will be automatically executed, so make sure it works without modifications.

YOU NEED TO BE MAKE SURE THAT THE GENERATED CODE IS CORRECT BASED ON THE FUSION API FOUND HERE: https://help.autodesk.com/view/fusion360/ENU/
"""

def process_message(message):
    """Process user message using Anthropic Claude"""
    try:
        # Enhance the user message if it doesn't explicitly ask for code
        if "code" not in message.lower() and "script" not in message.lower():
            enhanced_message = f"""
Create Fusion 360 Python code that will accomplish the following task:

{message}

IMPORTANT: Your code MUST be a complete, executable Fusion 360 script. Don't omit any necessary code sections.
Include proper error handling, and follow Fusion 360 API best practices exactly as specified.

The code WILL be directly executed in Fusion 360, so it needs to be complete and correct.
"""
        else:
            enhanced_message = message
            
        # Call the API with explicit error handling
        try:
            response = client.messages.create(
                model="claude-3-7-sonnet-latest",
                system=system_message,
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