// ===== SOUND PLAYER =====
function playSound(id) {
    const audio = document.getElementById(id);
    if (audio) {
        audio.currentTime = 0;   // rewind
        audio.volume = 1.0;
        audio.play().catch(err => {
            console.log("Audio blocked until first interaction:", err.message);
        });
    }
}

// ============ MAIN CHAT CLASS ============
class BertChat {
    constructor() {
        this.messagesContainer = document.getElementById("chatMessages");
        this.messageInput = document.getElementById("messageInput");
        this.sendBtn = document.getElementById("sendBtn");
        this.fileInput = document.getElementById("fileInput");
        this.quickRepliesContainer = document.getElementById("quickReplies");

        this.init();
    }

    init() {
        // Button click
        this.sendBtn.addEventListener("click", () => this.sendMessage());

        // Enter key
        this.messageInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // File upload
        this.fileInput.addEventListener("change", (e) => this.handleFileUpload(e));

        // Starter bot welcome
        setTimeout(() => {
            this.addBotMessage("🤖 Hello! I'm <b>Bert</b>, created by <b>Raval Dhwanil</b>. How can I help?");
            this.showQuickReplies(["What can you do?", "Who created you?", "Tell me a joke", "Help"]);
            playSound("receiveSound");
        }, 600);
    }

    // ========== SEND ==========
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addUserMessage(message);
        playSound("sendSound");
        this.messageInput.value = "";

        this.showTypingIndicator();

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        })
        .then(res => res.json())
        .then(data => {
            this.hideTypingIndicator();
            this.addBotMessage(data.response);
            playSound("receiveSound");
            if (data.quick_replies?.length) {
                this.showQuickReplies(data.quick_replies);
            }
        })
        .catch(() => {
            this.hideTypingIndicator();
            this.addBotMessage("⚠️ Connection error. Try again.");
        });
    }

    // ========== Add messages ==========
    addUserMessage(message) {
        const msg = this.createMessageElement(message, "user");
        this.messagesContainer.appendChild(msg);
        this.scrollToBottom();
        this.clearWelcome();
    }

    addBotMessage(message) {
        const msg = this.createMessageElement(message, "bot");
        this.messagesContainer.appendChild(msg);
        this.scrollToBottom();
    }

    createMessageElement(message, sender) {
        const wrapper = document.createElement("div");
        wrapper.className = `message ${sender}`;

        const bubble = document.createElement("div");
        bubble.className = "message-content";
        bubble.innerHTML = message.replace(/\n/g, "<br>");

        const time = document.createElement("div");
        time.className = "message-time";
        time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        bubble.appendChild(time);
        wrapper.appendChild(bubble);

        return wrapper;
    }

    // ========== Quick Replies ==========
    showQuickReplies(replies) {
        this.quickRepliesContainer.innerHTML = "";

        replies.forEach(reply => {
            const btn = document.createElement("button");
            btn.className = "quick-reply-btn";
            btn.textContent = reply;

            btn.addEventListener("click", () => {
                playSound("clickSound");
                this.messageInput.value = reply;
                this.sendMessage();
                this.quickRepliesContainer.innerHTML = "";
            });

            this.quickRepliesContainer.appendChild(btn);
        });
    }

    // ========== Typing Indicator ==========
    showTypingIndicator() {
        this.hideTypingIndicator();
        const typing = document.createElement("div");
        typing.className = "message bot typing-message";
        typing.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>`;
        this.messagesContainer.appendChild(typing);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typing = this.messagesContainer.querySelector(".typing-message");
        if (typing) typing.remove();
    }

    // ========== File Upload ==========
    handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        this.addUserMessage(`📎 Uploading: ${file.name}`);
        this.showTypingIndicator();

        const formData = new FormData();
        formData.append("file", file);

        fetch("/upload", { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {
            this.hideTypingIndicator();
            if (data.success) {
                this.addBotMessage(data.message);
                playSound("receiveSound");
            } else {
                this.addBotMessage(`❌ ${data.error}`);
            }
        });

        e.target.value = ""; // reset to allow same file again
    }

    // ========== Helpers ==========
    clearWelcome() {
        const welcome = document.querySelector(".welcome-message");
        if (welcome) welcome.remove();
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}

// ========== INIT APP ==========
window.addEventListener("DOMContentLoaded", () => {
    new BertChat();
});

// ===== IMPORTANT FIX: Unlock Audio Policy =====
// Chrome blocks audio until first click or keypress
function unlockAudio() {
    document.querySelectorAll("audio").forEach(a => {
        a.muted = false;
        a.play().then(() => a.pause()).catch(()=>{});
    });
}
window.addEventListener("click", unlockAudio, { once: true });
window.addEventListener("keydown", unlockAudio, { once: true });