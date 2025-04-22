// Display a welcome message when the chat is first loaded
document.addEventListener('DOMContentLoaded', function() {
    addSystemMessage(`Welcome to Fusion 360 GPT Chat! How can I help you today?
    
This chat now uses the Fusion 360 API documentation to generate reliable code!

Tips:
- Ask me to create 3D models and I'll generate code that follows best practices
- I'll automatically fix common API errors
- All generated code will be executed automatically
- If an error occurs, I'll try to fix it and run again`);

    // Set up the auto-resize functionality for the input box
    const inputBox = document.getElementById("inputBox");
    
    // Initial call to set the right height
    autoResizeTextarea(inputBox);
    
    // Add event listeners for input changes
    inputBox.addEventListener("input", function() {
        autoResizeTextarea(this);
    });
});

// Function to auto-resize the textarea
function autoResizeTextarea(element) {
    element.style.height = "auto"; // Reset height to recalculate
    element.style.height = (element.scrollHeight) + "px"; // Set new height based on content
}

// Add event listener for Enter key in the input box (but allow Shift+Enter for new lines)
document.getElementById("inputBox").addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// Function to add a user message to the chat
function addUserMessage(text) {
    const chatBox = document.getElementById("chatBox");
    const messageDiv = document.createElement("div");
    messageDiv.className = "message user-message";
    
    const senderDiv = document.createElement("div");
    senderDiv.className = "sender user";
    senderDiv.textContent = "You";
    
    const contentDiv = document.createElement("div");
    contentDiv.className = "content";
    contentDiv.textContent = text;
    
    messageDiv.appendChild(senderDiv);
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    
    scrollToBottom();
}

// Function to add a system (AI) message to the chat
function addSystemMessage(text) {
    const chatBox = document.getElementById("chatBox");
    const messageDiv = document.createElement("div");
    messageDiv.className = "message system-message";
    
    const senderDiv = document.createElement("div");
    senderDiv.className = "sender system";
    senderDiv.textContent = "Fusion GPT";
    
    const contentDiv = document.createElement("div");
    contentDiv.className = "content";
    
    // Check if the message contains code blocks and format them
    if (text.includes("```")) {
        let parts = text.split(/```(?:python)?/);
        let htmlContent = '';
        
        for (let i = 0; i < parts.length; i++) {
            if (i % 2 === 0) {
                // Regular text - replace line breaks with <br> and handle execution results specially
                let regularText = parts[i].replace(/\n/g, '<br>');
                htmlContent += `<p>${regularText}</p>`;
            } else {
                // Code block
                htmlContent += `<pre class="code-block"><code>${parts[i]}</code></pre>`;
            }
        }
        contentDiv.innerHTML = htmlContent;
    } else {
        contentDiv.innerHTML = text.replace(/\n/g, '<br>');
    }
    
    messageDiv.appendChild(senderDiv);
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    
    scrollToBottom();
    
    return messageDiv; // Return the message element in case we need to remove it later
}

// Function to add a loading indicator to the chat
function addLoadingIndicator(text) {
    const chatBox = document.getElementById("chatBox");
    const loadingContainer = document.createElement("div");
    loadingContainer.className = "loading-container";
    
    // Create loading bar
    const loadingBar = document.createElement("div");
    loadingBar.className = "loading-bar";
    
    const loadingBarProgress = document.createElement("div");
    loadingBarProgress.className = "loading-bar-progress";
    
    loadingBar.appendChild(loadingBarProgress);
    
    // Create loading text
    const loadingText = document.createElement("div");
    loadingText.className = "loading-text";
    loadingText.textContent = text || "Processing...";
    
    // Add elements to container
    loadingContainer.appendChild(loadingBar);
    loadingContainer.appendChild(loadingText);
    
    // Add to chat
    chatBox.appendChild(loadingContainer);
    scrollToBottom();
    
    return loadingContainer;
}

// Function to add a status indicator message
function addStatusIndicator(status, text) {
    const chatBox = document.getElementById("chatBox");
    const statusContainer = document.createElement("div");
    statusContainer.className = "status-container";
    
    const statusIndicator = document.createElement("div");
    statusIndicator.className = `status-indicator status-${status}`;
    
    let statusText = text;
    if (!statusText) {
        switch(status) {
            case "generating":
                statusText = "Generating API-compliant code...";
                break;
            case "executing":
                statusText = "Executing code...";
                break;
            case "fixing":
                statusText = "Auto-fixing API errors...";
                break;
            case "error":
                statusText = "Error occurred";
                break;
            default:
                statusText = "Processing...";
        }
    }
    
    statusIndicator.textContent = statusText;
    statusContainer.appendChild(statusIndicator);
    
    chatBox.appendChild(statusContainer);
    scrollToBottom();
    
    return statusContainer;
}

// Function to scroll the chat to the bottom
function scrollToBottom() {
    const chatBox = document.getElementById("chatBox");
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Store the last code block for reuse
let lastCodeBlock = "";

// Function to send a message to the server
function sendMessage() {
    const input = document.getElementById("inputBox");
    const text = input.value.trim();
    
    if (!text) return;
    
    // Add user message to chat
    addUserMessage(text);
    
    // Show loading indicator
    const loadingIndicator = addLoadingIndicator("Consulting API documentation...");
    
    // Also add a status indicator
    const statusIndicator = addStatusIndicator("generating", "Generating API-compliant code...");
    
    // Store any code blocks from recent system messages for reuse
    const codeBlocks = document.querySelectorAll('.system-message:last-of-type .code-block code');
    if (codeBlocks.length > 0) {
        lastCodeBlock = codeBlocks[codeBlocks.length - 1].textContent;
    }
    
    // Create data object to send
    const data = {
        arg1: text,
        arg2: lastCodeBlock // Pass the last code block for context/execution
    };
    
    // Clear input field and reset its height
    input.value = "";
    autoResizeTextarea(input);
    input.focus();
    
    // Send data to Fusion 360
    adsk.fusionSendData("chatMessage", JSON.stringify(data)).then((response) => {
        // Remove the loading and status indicators
        const chatBox = document.getElementById("chatBox");
        chatBox.removeChild(loadingIndicator);
        chatBox.removeChild(statusIndicator);
        
        // Check if response contains code that will be executed
        if (response.includes("```python")) {
            // Add an executing status indicator
            const executingIndicator = addStatusIndicator("executing", "Executing code...");
            
            // Add the response
            addSystemMessage(response);
            
            // Check if auto-fixing is happening
            if (response.includes("**Automatically fixing error**") || 
                response.includes("**Improved Solution:**")) {
                // Add a fixing indicator
                const fixingIndicator = addStatusIndicator("fixing", "Auto-fixing API errors...");
                
                // Remove indicators after a delay
                setTimeout(() => {
                    if (executingIndicator && executingIndicator.parentNode) {
                        executingIndicator.parentNode.removeChild(executingIndicator);
                    }
                    if (fixingIndicator && fixingIndicator.parentNode) {
                        fixingIndicator.parentNode.removeChild(fixingIndicator);
                    }
                }, 3000);
            } else {
                // Just remove the executing indicator after a delay
                setTimeout(() => {
                    if (executingIndicator && executingIndicator.parentNode) {
                        executingIndicator.parentNode.removeChild(executingIndicator);
                    }
                }, 2000);
            }
        } else {
            // Just add the response without execution indicator
            addSystemMessage(response);
        }
        
        // Check if a new code block exists in the response
        const newCodeBlocks = document.querySelectorAll('.system-message:last-of-type .code-block code');
        if (newCodeBlocks.length > 0) {
            lastCodeBlock = newCodeBlocks[newCodeBlocks.length - 1].textContent;
        }
        
        // Only add execute button if code is present but wasn't executed automatically
        if (response.includes("```python") && !response.includes("**Execution Result:**")) {
            addExecuteButton();
        }
    }).catch((error) => {
        // Remove the loading indicators
        const chatBox = document.getElementById("chatBox");
        chatBox.removeChild(loadingIndicator);
        chatBox.removeChild(statusIndicator);
        
        // Add error status
        const errorIndicator = addStatusIndicator("error", "Error: Could not process your request");
        
        // Add error message
        addSystemMessage("Error: Could not process your request. Please try again.");
        console.error(error);
        
        // Remove error indicator after a few seconds
        setTimeout(() => {
            if (errorIndicator && errorIndicator.parentNode) {
                errorIndicator.parentNode.removeChild(errorIndicator);
            }
        }, 5000);
    });
}

// Function to add an execute button
function addExecuteButton() {
    const chatBox = document.getElementById("chatBox");
    const buttonDiv = document.createElement("div");
    buttonDiv.className = "execute-button-container";
    
    const executeButton = document.createElement("button");
    executeButton.textContent = "Execute Code";
    executeButton.className = "execute-button";
    executeButton.onclick = function() {
        // Get latest code from the last message
        const codeBlocks = document.querySelectorAll('.system-message:last-of-type .code-block code');
        if (codeBlocks.length > 0) {
            lastCodeBlock = codeBlocks[codeBlocks.length - 1].textContent;
        }
        
        // Create a message that includes the /execute command
        const message = "Execute the previous code /execute";
        
        // Add user message to chat
        addUserMessage(message);
        
        // Show executing status
        const executingIndicator = addStatusIndicator("executing", "Executing code...");
        
        // Create data object to send
        const data = {
            arg1: message,
            arg2: lastCodeBlock // Pass the actual code to execute
        };
        
        // Send data to Fusion 360
        adsk.fusionSendData("chatMessage", JSON.stringify(data)).then((response) => {
            // Remove the executing indicator
            if (executingIndicator && executingIndicator.parentNode) {
                executingIndicator.parentNode.removeChild(executingIndicator);
            }
            
            // Add the actual response
            addSystemMessage(response);
        }).catch((error) => {
            // Remove the executing indicator
            if (executingIndicator && executingIndicator.parentNode) {
                executingIndicator.parentNode.removeChild(executingIndicator);
            }
            
            // Add error status
            const errorIndicator = addStatusIndicator("error", "Error: Could not execute the code");
            
            // Add error message
            addSystemMessage("Error: Could not execute the code. Please try again.");
            console.error(error);
            
            // Remove error indicator after a few seconds
            setTimeout(() => {
                if (errorIndicator && errorIndicator.parentNode) {
                    errorIndicator.parentNode.removeChild(errorIndicator);
                }
            }, 5000);
        });
    };
    
    buttonDiv.appendChild(executeButton);
    chatBox.appendChild(buttonDiv);
    
    scrollToBottom();
}