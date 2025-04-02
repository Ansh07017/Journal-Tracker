// Chat functionality for the Research Assistant

document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    const chatForm = document.getElementById('chat-form');
    const chatContainer = document.getElementById('chat-container');
    const typingIndicator = document.createElement('div');
    
    // Initialize chat container
    initChatContainer();
    
    // Set up typing indicator
    setupTypingIndicator();
    
    // Listen for form submission
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = chatInput.value.trim();
            
            if (message) {
                // Add user message to chat
                addMessageToChat('user', message);
                
                // Clear input
                chatInput.value = '';
                
                // Show typing indicator
                showTypingIndicator();
                
                // Send message to server
                sendMessageToServer(message);
            }
        });
    }
    
    // Function to initialize chat container with welcome message
    function initChatContainer() {
        if (!chatContainer) return;
        
        // Add welcome message
        const welcomeMessage = `
            <h5>Research Assistant</h5>
            <p>Welcome! I can help you with:</p>
            <ul>
                <li>Research paper management and search</li>
                <li>Patent search and analysis</li>
                <li>Literature summarization</li>
                <li>Citation generation</li>
                <li>Research workflow assistance</li>
            </ul>
            <p>How can I assist with your research today?</p>
        `;
        
        addMessageToChat('bot', welcomeMessage);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Function to set up typing indicator
    function setupTypingIndicator() {
        typingIndicator.className = 'chat-message bot-message typing-indicator';
        typingIndicator.innerHTML = `
            <div>
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        chatContainer.appendChild(typingIndicator);
        scrollToBottom();
    }
    
    // Function to hide typing indicator
    function hideTypingIndicator() {
        if (typingIndicator.parentNode === chatContainer) {
            chatContainer.removeChild(typingIndicator);
        }
    }
    
    // Function to add a message to the chat
    function addMessageToChat(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender === 'user' ? 'user-message' : 'bot-message'}`;
        
        // For bot messages, we may want to parse for Markdown-like formatting
        if (sender === 'bot') {
            // Simple formatting: Bold text between ** or __
            message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            message = message.replace(/__(.*?)__/g, '<strong>$1</strong>');
            
            // Italics between * or _
            message = message.replace(/\*(.*?)\*/g, '<em>$1</em>');
            message = message.replace(/_(.*?)_/g, '<em>$1</em>');
            
            // Convert URLs to links
            message = message.replace(
                /(https?:\/\/[^\s]+)/g, 
                '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
            );
            
            // Convert newlines to <br>
            message = message.replace(/\n/g, '<br>');
        } else {
            // For user messages, just escape HTML and handle newlines
            message = message
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;')
                .replace(/\n/g, '<br>');
        }
        
        messageDiv.innerHTML = message;
        chatContainer.appendChild(messageDiv);
        
        // Scroll to the bottom of the chat container
        scrollToBottom();
    }
    
    // Function to send message to server
    function sendMessageToServer(message) {
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response to chat
            addMessageToChat('bot', data.response);
        })
        .catch(error => {
            // Hide typing indicator
            hideTypingIndicator();
            
            console.error('Error:', error);
            addMessageToChat('bot', 'Sorry, I encountered an error processing your request. Please try again later.');
        });
    }
    
    // Function to scroll to the bottom of the chat container
    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    // Suggested questions functionality
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    if (suggestionButtons) {
        suggestionButtons.forEach(button => {
            button.addEventListener('click', function() {
                const question = this.textContent;
                chatInput.value = question;
                chatInput.focus();
            });
        });
    }
});
