import json
import traceback
import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ... import config
from datetime import datetime
from . import llm_client
from . import code_executor

app = adsk.core.Application.get()
ui = app.userInterface

# Command configuration
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_PalleteShow'
CMD_NAME = 'FusionGPT'
CMD_Description = 'A Fusion Add-in Palette'
PALETTE_NAME = 'FusionGPT'
IS_PROMOTED = True  # Make it more visible

# Using "global" variables by referencing values from /config.py
PALETTE_ID = config.sample_palette_id

# Specify the full path to the local html. You can also use a web URL
# such as 'https://www.autodesk.com/'
PALETTE_URL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'html', 'index.html')

# The path function builds a valid OS path. This fixes it to be a valid local URL.
PALETTE_URL = PALETTE_URL.replace('\\', '/')

# Set a default docking behavior for the palette
PALETTE_DOCKING = adsk.core.PaletteDockingStates.PaletteDockStateRight

# Define the location where the command button will be created
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    palette = ui.palettes.itemById(PALETTE_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the Palette
    if palette:
        palette.deleteMe()


# Event handler that is called when the user clicks the command button in the UI.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Command created event.')

    # Create the event handlers you will need for this instance of the command
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# Because no command inputs are being added in the command created event, the execute
# event is immediately fired.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Command execute event.')

    palettes = ui.palettes
    palette = palettes.itemById(PALETTE_ID)
    if palette is None:
        palette = palettes.add(
            id=PALETTE_ID,
            name=PALETTE_NAME,
            htmlFileURL=PALETTE_URL,
            isVisible=True,
            showCloseButton=True,
            isResizable=True,
            width=650,
            height=600,
            useNewWebBrowser=True
        )
        futil.add_handler(palette.closed, palette_closed)
        futil.add_handler(palette.navigatingURL, palette_navigating)
        futil.add_handler(palette.incomingFromHTML, palette_incoming)
        futil.log(f'{CMD_NAME}: Created a new palette: ID = {palette.id}, Name = {palette.name}')

    if palette.dockingState == adsk.core.PaletteDockingStates.PaletteDockStateFloating:
        palette.dockingState = PALETTE_DOCKING

    palette.isVisible = True


# Use this to handle a user closing your palette.
def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Palette was closed.')


# Use this to handle a user navigating to a new page in your palette.
def palette_navigating(args: adsk.core.NavigationEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Palette navigating event.')

    # Get the URL the user is navigating to:
    url = args.navigationURL

    log_msg = f"User is attempting to navigate to {url}\n"
    futil.log(log_msg, adsk.core.LogLevels.InfoLogLevel)

    # Check if url is an external site and open in user's default browser.
    if url.startswith("http"):
        args.launchExternally = True


# Use this to handle events sent from javascript in your palette.
def palette_incoming(html_args: adsk.core.HTMLEventArgs):
    try:
        # Parse the incoming data from the HTML
        data = json.loads(html_args.data)
        user_message = data.get('arg1', '')
        
        futil.log(f"Received message: {user_message}", adsk.core.LogLevels.InfoLogLevel)
        
        # Check if the user wants to execute code
        execute_code = "/execute" in user_message.lower()
        
        # If this is an execution command for previous code
        if user_message.lower().startswith("execute the previous code"):
            futil.log("Executing previous code command detected", adsk.core.LogLevels.InfoLogLevel)
            
            # This is the easiest way to extract the code directly from the pasted message
            code_to_execute = code_executor.extract_code(data.get('arg2', ''))
            
            if not code_to_execute:
                html_args.returnData = "No code found to execute. Please try again or provide code directly."
                return
                
            # Log the code for debugging
            futil.log(f"Executing code:\n{code_to_execute}", adsk.core.LogLevels.InfoLogLevel)
            
            # Execute the extracted code
            execution_result = code_executor.execute_code(code_to_execute)
            
            # Return the execution result
            html_args.returnData = f"Execution Result:\n```\n{execution_result}\n```"
            return
        
        # Normal message flow - get response from LLM
        response = llm_client.process_message(user_message)
        
        # Extract code from the response
        code_to_execute = code_executor.extract_code(response)
        
        # Always try to execute code if present (unless user explicitly says not to)
        if code_to_execute and ("don't execute" not in user_message.lower() and "do not execute" not in user_message.lower()):
            # Log the code being executed
            futil.log(f"Auto-executing code:\n{code_to_execute}", adsk.core.LogLevels.InfoLogLevel)
            
            try:
                # Execute the code
                execution_result = code_executor.execute_code(code_to_execute)
                
                # Append execution result to the response
                response += f"\n\n**Execution Result:**\n```\n{execution_result}\n```"
            except Exception as e:
                error_msg = f"Error during execution: {str(e)}\n{traceback.format_exc()}"
                futil.log(error_msg, adsk.core.LogLevels.ErrorLogLevel)
                response += f"\n\n**Execution Error:**\n```\n{error_msg}\n```"
        
        html_args.returnData = response
        
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}\n{traceback.format_exc()}"
        futil.log(error_msg, adsk.core.LogLevels.ErrorLogLevel)
        html_args.returnData = f"Error: {error_msg}"


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Command destroy event.')

    global local_handlers
    local_handlers = []