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

# System message defining assistant behavior with enhanced reliability guidance
system_message = """You are a Fusion 360 API expert. Generate executable Python code that creates 3D models using the Fusion 360 API.

IMPORTANT: All code you provide MUST be executable and reliable within Fusion 360. Avoid common API errors!

Follow these rules when writing Fusion 360 code:

1. ALWAYS place ALL code inside a run(context) function with COMPREHENSIVE error handling:
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

2. AVOID THESE COMMON GEOMETRY ERRORS:
   - For revolve operations: NEVER create paths that are tangent to profiles
   - For extrude operations: NEVER extrude zero-area profiles
   - For sketches: ALWAYS check that profiles are closed before operations
   - For loft/sweep: Ensure start and end profiles have compatible topology
   - Check that construction planes are valid before using them
   - ALWAYS use ValueInput correctly: createByReal() for simple values, createByString() for values with units

3. IMPLEMENT DEFENSIVE CODING:
   - Add validation checks BEFORE performing operations
   - Verify that sketches contain valid profiles before using them
   - For revolve operations, ensure rotation axis doesn't intersect profile
   - For Boolean operations, verify bodies exist before operations
   - Use try/except blocks around EACH major operation

4. ALWAYS initialize these core variables:
   - app = adsk.core.Application.get()
   - ui = app.userInterface
   - design = app.activeProduct
   - rootComp = design.rootComponent

5. Properly scope ALL variables - especially in event handlers.

6. For complicated geometry, use SIMPLER approaches:
   - Prefer multiple simple operations over complex ones
   - For complex shapes, build them using basic primitives
   - Use construction planes to establish reliable references
   - When creating curves, use minimum number of control points

7. When working with standard components like holes, slots, or fillets:
   - Use the built-in features rather than manual geometry
   - Apply proper parameters for these features

8. For operations with multiple inputs (like loft/sweep):
   - Validate EACH input separately 
   - Use extra validation calculations

Remember, your code will be directly executed. ALWAYS include validation checks before geometry operations.
"""

def process_message(message):
    """Process user message using Anthropic Claude with improved reliability prompting"""
    try:
        # Enhance the user message to focus on reliability
        if any(keyword in message.lower() for keyword in ["create", "make", "generate", "model", "build", "design"]):
            enhanced_message = f"""
Create reliable Fusion API Python code that will accomplish this task:

{message}

IMPORTANT:
1. Your code must be COMPLETE and EXECUTABLE
2. Include VALIDATION CHECKS before each geometry operation
3. Use DEFENSIVE CODING to prevent common errors
4. For revolve operations, ensure the axis is NOT tangent to the profile
5. For extrudes, ensure profiles are valid and closed
6. Add helpful comments explaining your approach
7. If the request is complex, simplify the approach

The code WILL be directly executed in Fusion, so it needs to be robust against API errors.

PLEASE MAKE SURE YOU ARE USING THE CORRECT CODE FROM THE FUSION WEBSITE: https://help.autodesk.com/view/fusion360/ENU/
"""
        else:
            enhanced_message = message
            
        # Call the API with explicit error handling
        try:
            response = client.messages.create(
                model="claude-3-7-sonnet-latest",
                system=system_message,
                max_tokens= 20000,
                messages=[{"role": "user", "content": enhanced_message}]
            )
            return response.content[0].text
        except Exception as api_error:
            error_details = f"API Error: {str(api_error)}\n{traceback.format_exc()}"
            return f"Error communicating with Claude: {error_details}"
            
    except Exception as e:
        error_details = f"Processing Error: {str(e)}\n{traceback.format_exc()}"
        return f"Error processing message: {error_details}"