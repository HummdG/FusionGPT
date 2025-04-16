import adsk.core
import adsk.fusion
import tempfile
import os
import traceback
import sys
import importlib.util
import inspect
import re

app = adsk.core.Application.get()
ui = app.userInterface

def validate_code(code):
    """
    Validate Fusion 360 code for common pitfalls and API issues
    
    Args:
        code (str): The Python code to validate
    
    Returns:
        tuple: (is_valid, issues) - Boolean indicating if code passed validation and list of issues
    """
    issues = []
    
    # Check for basic structure
    if "def run(context)" not in code:
        issues.append("Missing run(context) function definition")
    
    if "try:" not in code or "except" not in code:
        issues.append("Missing proper error handling (try/except blocks)")
    
    # Check for initialization of core variables
    required_initializations = [
        "app = adsk.core.Application.get()",
        "ui = app.userInterface",
    ]
    
    for init in required_initializations:
        if init not in code:
            issues.append(f"Missing core initialization: {init}")
    
    # Check for common API issues
    
    # Revolve operation issues (common cause of failures)
    if "revolve" in code.lower() or "revolvefeatures" in code.lower():
        # Check if code contains validation for revolve axis
        if not any(check in code.lower() for check in [
            "check", "validate", "ensure", "verify", "confirm", "test"
        ]) and "axis" in code.lower():
            issues.append("WARNING: Revolve operation without explicit axis validation")
    
    # Extrude operation issues
    if "extrude" in code.lower() or "extrudefeatures" in code.lower():
        if not any(check in code.lower() for check in [
            "check", "validate", "ensure", "verify", "profiles", "isValid"
        ]):
            issues.append("WARNING: Extrude operation without profile validation")
    
    # Check for proper ValueInput usage
    value_input_pattern = re.compile(r'ValueInput\.create\w+\(([^)]+)\)')
    for match in value_input_pattern.finditer(code):
        value = match.group(1).strip()
        if "createByReal" in match.group(0) and ('"' in value or "'" in value):
            issues.append("WARNING: Using createByReal with string values - use createByString for units")
    
    # Check for event handler scoping issues
    if "def " in code and "handler" in code.lower():
        if "global " not in code and "nonlocal " not in code:
            issues.append("WARNING: Event handlers defined without proper variable scoping (global/nonlocal)")
    
    is_valid = len(issues) == 0 or all("WARNING" in issue for issue in issues)
    return is_valid, issues

def execute_code(code):
    """
    Execute Fusion 360 API code provided by the LLM with additional validation
    
    Args:
        code (str): The Python code to execute
    
    Returns:
        str: Result of the execution
    """
    try:
        # Validate the code first
        is_valid, issues = validate_code(code)
        
        # Log validation results
        if issues:
            validation_message = "Code validation found the following issues:\n- " + "\n- ".join(issues)
            futil_log = f"Code validation issues: {issues}"
            
            # If critical issues exist, alert the user but continue anyway
            if not is_valid:
                ui.messageBox(validation_message + "\n\nAttempting to run anyway, but execution may fail.")
                return f"VALIDATION FAILED: {validation_message}\n\nExecution aborted."
        
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
            
            # Try to provide more helpful error messages for common issues
            if "revolve" in code.lower() and "tangent" in str(e).lower():
                error_msg += "\n\nSUGGESTION: The revolve operation failed because the axis is tangent to or intersects the profile. Try adjusting the axis location or the profile geometry."
            elif "extrude" in code.lower() and "profile" in str(e).lower():
                error_msg += "\n\nSUGGESTION: The extrude operation failed, likely due to an invalid profile. Check that the sketch contains closed profiles and that the correct profile is selected."
            elif "boolean" in code.lower() and "body" in str(e).lower():
                error_msg += "\n\nSUGGESTION: The boolean operation failed. Verify that all target bodies exist and are valid before the operation."
            
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