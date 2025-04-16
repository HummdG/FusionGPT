// Display a welcome message when the chat is first loaded
document.addEventListener('DOMContentLoaded', function() {
    addSystemMessage(`Welcome to Fusion 360 GPT Chat! How can I help you today?
    
Tips:
- Ask for Fusion 360 API code samples
- Use "/execute" at the end of your message to automatically run generated code
- Be specific about what you want to achieve`);
});

// Add event listener for Enter key in the input box
document.getElementById("inputBox").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
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
}

// Function to scroll the chat to the bottom
function scrollToBottom() {
    const chatBox = document.getElementById("chatBox");
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Function to send a message to the server
function sendMessage() {
    const input = document.getElementById("inputBox");
    const text = input.value.trim();
    
    if (!text) return;
    
    // Add user message to chat
    addUserMessage(text);
    
    // Show loading indicator
    const loadingMessage = "Processing your request...";
    addSystemMessage(loadingMessage);
    
    // Create data object to send
    const data = {
        arg1: text,
        arg2: new Date().toISOString()
    };
    
    // Clear input field
    input.value = "";
    input.focus();
    
    // Send data to Fusion 360
    adsk.fusionSendData("chatMessage", JSON.stringify(data)).then((response) => {
        // Remove the loading message
        const chatBox = document.getElementById("chatBox");
        chatBox.removeChild(chatBox.lastChild);
        
        // Add the actual response
        addSystemMessage(response);
        
        // Add execute button if code is present and execution wasn't already requested
        if (response.includes("```python") && !text.toLowerCase().includes("/execute")) {
            addExecuteButton();
        }
    }).catch((error) => {
        // Remove the loading message
        const chatBox = document.getElementById("chatBox");
        chatBox.removeChild(chatBox.lastChild);
        
        // Add error message
        addSystemMessage("Error: Could not process your request. Please try again.");
        console.error(error);
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
        const lastSystemMessage = document.querySelector(".system-message:last-of-type .content");
        
        // Get code from the last message
        let codeContent = "";
        if (lastSystemMessage) {
            const codeBlock = lastSystemMessage.querySelector("pre.code-block code");
            if (codeBlock) {
                codeContent = codeBlock.textContent;
            }
        }
        
        // Create a message that includes the /execute command
        const message = "Execute the previous code /execute";
        
        // Add user message to chat
        addUserMessage(message);
        
        // Show loading indicator
        const loadingMessage = "Executing code...";
        addSystemMessage(loadingMessage);
        
        // Create data object to send
        const data = {
            arg1: message,
            arg2: new Date().toISOString()
        };
        
        // Send data to Fusion 360
        adsk.fusionSendData("chatMessage", JSON.stringify(data)).then((response) => {
            // Remove the loading message
            const chatBox = document.getElementById("chatBox");
            chatBox.removeChild(chatBox.lastChild);
            
            // Add the actual response
            addSystemMessage(response);
        }).catch((error) => {
            // Remove the loading message
            const chatBox = document.getElementById("chatBox");
            chatBox.removeChild(chatBox.lastChild);
            
            // Add error message
            addSystemMessage("Error: Could not execute the code. Please try again.");
            console.error(error);
        });
    };
    
    buttonDiv.appendChild(executeButton);
    chatBox.appendChild(buttonDiv);
    
    scrollToBottom();
}