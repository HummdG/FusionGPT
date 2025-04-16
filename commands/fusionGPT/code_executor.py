import adsk.core
import adsk.fusion
import tempfile
import os
import traceback
import sys
import importlib.util
import inspect

app = adsk.core.Application.get()
ui = app.userInterface

def execute_code(code):
    """
    Execute Fusion 360 API code provided by the LLM
    
    Args:
        code (str): The Python code to execute
    
    Returns:
        str: Result of the execution
    """
    try:
        # Log that we're starting execution
        ui.messageBox("Starting code execution")
        
        # Create a temporary file with the generated code
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as temp_file:
            # Don't modify the code - directly write it to the file
            temp_file.write(code)
            temp_path = temp_file.name
        
        # Execute the code directly in the Fusion 360 environment
        try:
            # Import the module dynamically
            module_name = os.path.basename(temp_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, temp_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if there's a run function in the module
            if hasattr(module, 'run'):
                # Call the run function, passing None as context
                result = module.run(None)
                message = "Code executed successfully."
                if result:
                    message += f" Result: {result}"
                return message
            else:
                # If no run function exists, execute the code directly
                # This is a fallback and less ideal
                exec(code)
                return "Code executed directly (no run function found)."
            
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}\n{traceback.format_exc()}"
            ui.messageBox(error_msg)
            return error_msg
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
        
    except Exception as e:
        error_msg = f"Error preparing code: {str(e)}\n{traceback.format_exc()}"
        ui.messageBox(error_msg)
        return error_msg

def extract_code(message):
    """
    Extract Python code blocks from a message
    
    Args:
        message (str): Message containing code blocks
    
    Returns:
        str: The extracted code or None
    """
    if '```python' in message and '```' in message.split('```python', 1)[1]:
        return message.split('```python', 1)[1].split('```', 1)[0].strip()
    elif '```' in message:
        # Try to extract code from generic code blocks
        return message.split('```', 1)[1].split('```', 1)[0].strip()
    return None

def indent_code(code, spaces=4):
    """
    Indent each line of code by the specified number of spaces
    
    Args:
        code (str): The code to indent
        spaces (int): Number of spaces to indent
    
    Returns:
        str: Indented code
    """
    if not code:
        return ""
    
    indent = " " * spaces
    return indent + code.replace("\n", f"\n{indent}")