import adsk.core
import adsk.fusion
import tempfile
import os
import traceback
import sys

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
        # Create a temporary file with the generated code
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as temp_file:
            # Wrap the code in a main function with proper error handling
            wrapped_code = f"""import traceback
import adsk.core
import adsk.fusion

# Initialize the global variables
app = adsk.core.Application.get()
ui = app.userInterface

def run(context):
    try:
{indent_code(code, 8)}
        return "Code executed successfully"
    except Exception as e:
        if ui:
            ui.messageBox(f'Failed:\\n{{traceback.format_exc()}}')
        print(f'Failed:\\n{{traceback.format_exc()}}')
        return f'Error: {{str(e)}}'
"""
            temp_file.write(wrapped_code)
            temp_path = temp_file.name
        
        # Instead of using executeScript (which doesn't exist), we'll execute the code directly
        try:
            # Get the script path and make it available for import
            script_dir = os.path.dirname(temp_path)
            script_name = os.path.basename(temp_path).replace('.py', '')
            
            # Store current working directory
            original_cwd = os.getcwd()
            sys.path.insert(0, script_dir)
            
            # Create a namespace for the script
            script_namespace = {}
            
            # Execute the code
            with open(temp_path, 'r') as f:
                script_code = f.read()
                exec(script_code, script_namespace)
            
            # Call the run function
            result = script_namespace['run'](None)
            
            # Reset path
            sys.path.remove(script_dir)
            
            # Delete the temporary file
            os.unlink(temp_path)
            
            return result if result else "Code executed successfully"
            
        except Exception as e:
            return f"Error executing code: {str(e)}\n{traceback.format_exc()}"
        
    except Exception as e:
        return f"Error preparing code: {str(e)}\n{traceback.format_exc()}"

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