// js/chat.js - AI Chatbot

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    input.value = '';
    input.disabled = true;

    try {
        const response = await sendChatMessage(message);
        addMessage('assistant', response.response);
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
        input.disabled = false;
        input.focus();
    }
}

function addMessage(role, content) {
    const container = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🤖';
    const isUser = role === 'user';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${isUser ? content : formatAssistantMessage(content)}
        </div>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function formatAssistantMessage(content) {
    // Convert newlines to <br>
    let html = content.replace(/\n/g, '<br>');
    
    // Convert bullet points
    html = html.replace(/• /g, '• ');
    
    // Convert bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert lists
    if (html.includes('•')) {
        const parts = html.split('<br>');
        let inList = false;
        html = parts.map(p => {
            if (p.trim().startsWith('•')) {
                if (!inList) { inList = true; return `<ul><li>${p.trim().substring(1).trim()}</li>`; }
                return `<li>${p.trim().substring(1).trim()}</li>`;
            } else if (inList) {
                inList = false;
                return `</ul>${p}`;
            }
            return p;
        }).join('<br>');
        if (inList) html += '</ul>';
    }
    
    return html;
}

// ─── Event Listeners ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendChatBtn');

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});