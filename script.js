const messagesContainer = document.getElementById('messages-container');
const chatViewport = document.getElementById('chat-viewport');
const welcomeMessage = document.querySelector('.welcome-message');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const contextBtn = document.getElementById('pet-context-btn');
const drawer = document.getElementById('context-drawer');
const saveContextBtn = document.getElementById('save-context-btn');
const closeDrawerBtn = document.getElementById('close-drawer-btn');
const refreshChatBtn = document.getElementById('refresh-chat-btn');
const petContextInput = document.getElementById('pet-context-input');

let petContext = localStorage.getItem('nanu_pet_context') || "";
petContextInput.value = petContext;

let chatHistory = JSON.parse(localStorage.getItem('nanu_chat_history') || '[]');

if (chatHistory.length > 0) {
    welcomeMessage.classList.add('hidden');
    chatHistory.forEach(msg => {
        const div = document.createElement('div');
        div.className = `message ${msg.role}`;
        div.innerText = msg.content;
        messagesContainer.appendChild(div);
    });
    setTimeout(() => scrollChatToBottom('auto'), 50);
}

// --- UI Helpers ---

function scrollChatToBottom(behavior = 'smooth') {
    chatViewport.scrollTo({ top: chatViewport.scrollHeight, behavior });
}

function addMessage(text, sender, isStreaming = false) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    welcomeMessage.classList.add('hidden');
    if (isStreaming) {
        div.innerText = '';
        messagesContainer.appendChild(div);
        return streamText(div, text);
    } else {
        div.innerText = text;
        messagesContainer.appendChild(div);
        scrollChatToBottom();
    }
}

async function streamText(element, text) {
    const words = text.split(' ');
    for (let i = 0; i < words.length; i++) {
        element.innerText += (i === 0 ? '' : ' ') + words[i];
        scrollChatToBottom('auto');
        await new Promise(r => setTimeout(r, 40 + Math.random() * 40));
    }
    return Promise.resolve();
}



function updateStatus(status) {
    const statusText = document.querySelector('.status');
    if (status === 'online') {
        statusText.innerText = 'Here with you';
        statusText.style.color = 'var(--text-muted)';
    } else if (status === 'fallback') {
        statusText.innerText = 'Thinking with care';
        statusText.style.color = 'var(--text-muted)';
    }
}

// --- Logic ---

async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    chatHistory.push({ role: 'user', content: text });
    localStorage.setItem('nanu_chat_history', JSON.stringify(chatHistory));
    userInput.value = '';

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message nanu typing-indicator';
    typingDiv.innerText = 'Nanu is thinking...';
    messagesContainer.appendChild(typingDiv);
    welcomeMessage.classList.add('hidden');
    scrollChatToBottom();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, context: petContext, history: chatHistory.slice(-12) })
        });

        messagesContainer.removeChild(typingDiv);

        if (response.ok) {
            const raw = await response.text();
            const data = JSON.parse(raw);
            updateStatus('online');
            const finalMessage = data.message || simulateNanu(text).message;
            await addMessage(finalMessage, 'nanu', true);
            chatHistory.push({ role: 'nanu', content: finalMessage });
            localStorage.setItem('nanu_chat_history', JSON.stringify(chatHistory));
        } else {
            throw new Error("Server Error");
        }
    } catch (err) {
        if (messagesContainer.contains(typingDiv)) messagesContainer.removeChild(typingDiv);
        const fallback = simulateNanu(text);
        await addMessage(fallback.message, 'nanu', true);
    }
}

function simulateNanu(msg) {
    const lower = msg.toLowerCase();

    if (lower.includes('shivering') || lower.includes('seizure') || lower.includes('blood') || lower.includes('breathing') || lower.includes('poison')) {
        return {
            message: "This sounds urgent for your pet. You should go to a vet immediately. If your pet may have swallowed something harmful or cannot breathe normally, please leave now. Can you get to an emergency vet right away?"
        };
    }

    return {
        message: "I can see you're worried about your pet. That kind of change can feel unsettling. Keep them comfortable, offer water, and watch for any clear change in energy, appetite, or breathing. What changed first?"
    };
}

// --- Event Listeners ---

refreshChatBtn.onclick = () => {
    localStorage.removeItem('nanu_chat_history');
    location.reload();
};

sendBtn.onclick = handleSend;
userInput.onkeypress = (e) => { if (e.key === 'Enter') handleSend(); };

contextBtn.onclick = () => drawer.classList.remove('hidden');
closeDrawerBtn.onclick = () => drawer.classList.add('hidden');

saveContextBtn.onclick = () => {
    petContext = petContextInput.value;
    localStorage.setItem('nanu_pet_context', petContext);
    drawer.classList.add('hidden');
    addMessage("Thank you for sharing that. I've noted down these details about your pet to help me guide you better.", 'nanu', true);
};
