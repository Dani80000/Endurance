const state = {
    socket: null,
    username: "",
    password: "",
    loggedIn: false,
    intentionallyClosed: false,
    reconnectAttempts: 0,
    currentChannel: "General",
    chatData: { General: [] },
    presence: [],
    heartbeatId: null,
    reconnectId: null,
    typingSendId: null,
    typingClearId: null,
};

const els = {
    username: document.getElementById("username"),
    password: document.getElementById("password"),
    status: document.getElementById("status-text"),
    login: document.getElementById("login-button"),
    create: document.getElementById("create-button"),
    loginSection: document.getElementById("login-section"),
    chatSection: document.getElementById("chat-section"),
    chatTitle: document.getElementById("chat-title"),
    presence: document.getElementById("presence-list"),
    history: document.getElementById("chat-history"),
    typing: document.getElementById("typing-status"),
    message: document.getElementById("message-input"),
    send: document.getElementById("send-button"),
    emojiButton: document.getElementById("emoji-button"),
    emojiPicker: document.getElementById("emoji-picker"),
    fileInput: document.getElementById("file-input"),
    fileButton: document.getElementById("file-button"),
    dmUser: document.getElementById("dm-user-input"),
    dm: document.getElementById("dm-button"),
    serverButton: document.getElementById("server-button"),
    logout: document.getElementById("logout-button"),
};

const emojiList = [
    "🙂", "😀", "😂", "🤣", "😊", "😍", "😎",
    "🥳", "😅", "😭", "😤", "😡", "🤔", "🙃",
    "👍", "👎", "👏", "🙌", "🙏", "💪", "🤝",
    "❤️", "🔥", "✨", "✅", "❌", "⚠️", "💯",
    "💀", "👀", "🎉", "🚀", "🍕", "☕", "💻",
    "📎", "🔒", "🔑", "🛡️", "📣", "🧠", "🐛"
];

const maxUploadBytes = 5 * 1024 * 1024;
const usernamePattern = /^[a-z0-9_]{3,24}$/;
const minPasswordLength = 8;
const blockedFileExtensions = new Set([
    "ade", "adp", "apk", "app", "appx", "bat", "bin", "cmd", "com", "cpl",
    "dll", "dmg", "exe", "gadget", "hta", "ins", "iso", "jar", "js", "jse",
    "lnk", "msc", "msi", "msp", "mst", "ps1", "psm1", "reg", "scr", "sh",
    "sys", "vb", "vbe", "vbs", "ws", "wsc", "wsf", "wsh"
]);
const blockedMimeTypes = new Set([
    "application/x-msdownload",
    "application/x-msdos-program",
    "application/x-ms-installer",
    "application/x-sh",
    "application/java-archive",
    "text/javascript"
]);
const eicarSignature = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*";

function getWebSocketUrl() {
    if (window.SECURECHAT_WS_URL) {
        return window.SECURECHAT_WS_URL;
    }

    return "wss://secure-chat-bs75.onrender.com/ws";
}

function setStatus(message, isError = false) {
    els.status.textContent = message;
    els.status.classList.toggle("error", isError);
}

function showLocalSystemMessage(message) {
    if (state.loggedIn) {
        pushMessage({ sender: "SYSTEM", message, channel: state.currentChannel });
        return;
    }

    setStatus(message, true);
}

function capitalizeName(name) {
    return name ? name.charAt(0).toUpperCase() + name.slice(1) : "";
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
    }[char]));
}

function formatMessage(text) {
    let richText = escapeHtml(text);
    richText = richText.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
    richText = richText.replace(/\*(.*?)\*/g, "<i>$1</i>");
    richText = richText.replace(/(^|\s)(https?:\/\/[^\s<]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
    return richText.replace(/\n/g, "<br>");
}

function formatPayload(content) {
    if (typeof content === "object" && content !== null && content.type === "file") {
        if (content.download_error) {
            return escapeHtml(content.download_error);
        }

        const filename = escapeHtml(content.filename || "file");
        const data = String(content.data || "");
        return `<a href="${data}" download="${filename}">Download ${filename}</a>`;
    }

    return formatMessage(content);
}

function normalizeDmChannel(user1, user2) {
    return `dm_${[user1.trim().toLowerCase(), user2.trim().toLowerCase()].sort().join("_")}`;
}

function renderMessage(message) {
    const sender = message.sender || "SYSTEM";
    const content = message.message ?? "";
    const div = document.createElement("div");

    div.className = "msg";
    if (sender === "SYSTEM") div.classList.add("system");
    else if (sender === state.username) div.classList.add("self");
    else div.classList.add("other");

    div.innerHTML = `<b>${capitalizeName(escapeHtml(sender))}</b>: ${formatPayload(content)}`;
    return div;
}

function refreshChat() {
    const messages = state.chatData[state.currentChannel] || [];
    els.history.innerHTML = "";
    messages.forEach(message => els.history.appendChild(renderMessage(message)));
    els.history.scrollTop = els.history.scrollHeight;
}

function refreshPresence() {
    const users = state.presence.length ? state.presence : [state.username];
    els.presence.innerHTML = "";

    users.forEach(user => {
        const button = document.createElement("button");
        const isSelf = user === state.username;
        button.className = "presence-user";
        button.type = "button";
        button.textContent = isSelf ? `${capitalizeName(user)} (you)` : capitalizeName(user);
        button.disabled = isSelf;
        button.addEventListener("click", () => switchToDm(user));
        els.presence.appendChild(button);
    });
}

function pushMessage(message) {
    const channel = message.channel || "General";
    if (!state.chatData[channel]) state.chatData[channel] = [];
    state.chatData[channel].push(message);
    if (channel === state.currentChannel) refreshChat();
}

function switchToChat() {
    els.loginSection.hidden = true;
    els.loginSection.style.display = "none";
    els.chatSection.hidden = false;
    els.chatSection.style.display = "grid";
    state.currentChannel = "General";
    els.chatTitle.textContent = "Server";
    refreshPresence();
    refreshChat();
    startHeartbeat();
}

function requestHistory(channel) {
    if (state.socket?.readyState === WebSocket.OPEN) {
        state.socket.send(JSON.stringify({ action: "get_history", channel }));
    }
}

function connect(action, isReconnect = false) {
    const username = els.username.value.trim().toLowerCase();
    const password = els.password.value;
    const url = getWebSocketUrl();

    if (!usernamePattern.test(username)) {
        setStatus("Username must be 3-24 characters and use only lowercase letters, numbers, and underscores.", true);
        return;
    }

    if (password.length < minPasswordLength) {
        setStatus(`Password must be at least ${minPasswordLength} characters.`, true);
        return;
    }

    if (action === "login") {
        state.password = password;
    }

    setStatus(isReconnect ? "Reconnecting..." : "Connecting...");
    state.username = username;
    state.intentionallyClosed = false;

    const socket = new WebSocket(url);
    state.socket = socket;
    const connectTimeoutId = window.setTimeout(() => {
        if (socket.readyState === WebSocket.CONNECTING) {
            socket.close();
            setStatus("Connection timed out. Check that config.js points to the Render /ws URL.", true);
        }
    }, 10000);
    const authTimeoutId = window.setTimeout(() => {
        if (socket.readyState === WebSocket.OPEN) {
            socket.close();
            setStatus("Server connected but did not answer login. Check Render logs.", true);
        }
    }, 15000);

    socket.addEventListener("open", () => {
        window.clearTimeout(connectTimeoutId);
        setStatus("Authenticating...");
        socket.send(JSON.stringify({ action, user_id: username, password, channel: "General" }));
    });

    socket.addEventListener("message", event => {
        window.clearTimeout(authTimeoutId);
        const data = JSON.parse(event.data);

        if (data.status === "success") {
            if (action === "create") {
                setStatus("Account created. You can log in now.");
                socket.close();
                return;
            }

            setStatus(data.message || "Connected.");
            state.loggedIn = true;
            state.reconnectAttempts = 0;
            state.chatData.General = data.history || [];
            switchToChat();
            return;
        }

        if (data.status === "error") {
            setStatus(data.message || "Unable to connect.", true);
            socket.close();
            return;
        }

        if (data.action === "pong") {
            return;
        }

        if (data.action === "presence_update") {
            state.presence = data.users || [];
            refreshPresence();
            return;
        }

        if (data.action === "typing" && data.sender !== state.username && data.channel === state.currentChannel) {
            els.typing.textContent = `${capitalizeName(data.sender)} is typing...`;
            window.clearTimeout(state.typingClearId);
            state.typingClearId = window.setTimeout(() => {
                els.typing.textContent = "";
            }, 2200);
            return;
        }

        if (data.action === "history_update") {
            state.chatData[data.channel || "General"] = data.history || [];
            refreshChat();
            return;
        }

        if (data.sender === state.username) {
            return;
        }

        pushMessage(data);
    });

    socket.addEventListener("close", () => {
        window.clearTimeout(connectTimeoutId);
        window.clearTimeout(authTimeoutId);
        window.clearInterval(state.heartbeatId);
        if (!els.chatSection.hidden) {
            pushMessage({ sender: "SYSTEM", message: "Disconnected from server.", channel: state.currentChannel });
        }
        scheduleReconnect();
    });

    socket.addEventListener("error", () => {
        window.clearTimeout(connectTimeoutId);
        window.clearTimeout(authTimeoutId);
        setStatus("Could not connect to the WebSocket server.", true);
    });
}

function startHeartbeat() {
    window.clearInterval(state.heartbeatId);
    state.heartbeatId = window.setInterval(() => {
        if (state.socket?.readyState === WebSocket.OPEN) {
            state.socket.send(JSON.stringify({
                action: "ping",
                channel: state.currentChannel,
            }));
        }
    }, 25000);
}

function scheduleReconnect() {
    if (!state.loggedIn || state.intentionallyClosed || state.reconnectAttempts >= 5) return;

    state.reconnectAttempts += 1;
    const delay = Math.min(30000, 1000 * (2 ** (state.reconnectAttempts - 1)));
    window.clearTimeout(state.reconnectId);
    state.reconnectId = window.setTimeout(() => {
        if (state.socket?.readyState === WebSocket.OPEN) return;
        els.username.value = state.username;
        els.password.value = state.password;
        connect("login", true);
    }, delay);
}

function sendMessage() {
    const text = els.message.value;
    if (!text.trim() || state.socket?.readyState !== WebSocket.OPEN) return;

    state.socket.send(JSON.stringify({
        action: "send_message",
        user_id: state.username,
        message: text,
        channel: state.currentChannel,
    }));
    pushMessage({ sender: state.username, message: text, channel: state.currentChannel });
    els.message.value = "";
}

function sendTyping() {
    if (state.socket?.readyState !== WebSocket.OPEN) return;

    window.clearTimeout(state.typingSendId);
    state.typingSendId = window.setTimeout(() => {
        state.socket.send(JSON.stringify({
            action: "typing",
            channel: state.currentChannel,
        }));
    }, 250);
}

function renderEmojiPicker() {
    els.emojiPicker.innerHTML = "";
    emojiList.forEach(emoji => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "emoji-option";
        button.textContent = emoji;
        button.addEventListener("click", () => insertEmoji(emoji));
        els.emojiPicker.appendChild(button);
    });
}

function insertEmoji(emoji) {
    const input = els.message;
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? input.value.length;
    input.value = `${input.value.slice(0, start)}${emoji}${input.value.slice(end)}`;
    input.focus();
    input.selectionStart = input.selectionEnd = start + emoji.length;
    els.emojiPicker.hidden = true;
}

function toggleEmojiPicker(event) {
    event.stopPropagation();
    els.emojiPicker.hidden = !els.emojiPicker.hidden;
}

function getFileExtension(filename) {
    const parts = filename.toLowerCase().split(".");
    return parts.length > 1 ? parts.pop() : "";
}

function hasSuspiciousDoubleExtension(filename) {
    const parts = filename.toLowerCase().split(".").filter(Boolean);
    if (parts.length < 3) return false;
    return blockedFileExtensions.has(parts[parts.length - 1]) || blockedFileExtensions.has(parts[parts.length - 2]);
}

async function validateFileBeforeSend(file) {
    const extension = getFileExtension(file.name);

    if (file.size <= 0) {
        return "File is empty.";
    }

    if (file.size > maxUploadBytes) {
        return "File is too large. Maximum allowed size is 5 MB.";
    }

    if (blockedFileExtensions.has(extension)) {
        return `Blocked potentially dangerous file type: .${extension}`;
    }

    if (hasSuspiciousDoubleExtension(file.name)) {
        return "Blocked suspicious double-extension filename.";
    }

    if (file.type && blockedMimeTypes.has(file.type.toLowerCase())) {
        return `Blocked potentially dangerous MIME type: ${file.type}`;
    }

    const sample = await file.slice(0, Math.min(file.size, 65536)).text();
    if (sample.includes(eicarSignature)) {
        return "Blocked EICAR antivirus test signature.";
    }

    if (/<script[\s>]/i.test(sample) && ["html", "htm", "svg", "xml"].includes(extension)) {
        return "Blocked active script content in uploaded markup.";
    }

    return "";
}

async function sendFile() {
    const file = els.fileInput.files[0];
    if (!file || state.socket?.readyState !== WebSocket.OPEN) return;

    const validationError = await validateFileBeforeSend(file);
    if (validationError) {
        showLocalSystemMessage(`Upload blocked: ${validationError}`);
        els.fileInput.value = "";
        return;
    }

    const reader = new FileReader();
    reader.onload = () => {
        const payload = {
            type: "file",
            filename: file.name,
            data: reader.result,
        };

        state.socket.send(JSON.stringify({
            action: "send_message",
            user_id: state.username,
            message: payload,
            channel: state.currentChannel,
        }));
        pushMessage({ sender: state.username, message: payload, channel: state.currentChannel });
        els.fileInput.value = "";
    };
    reader.readAsDataURL(file);
}

function switchToServer() {
    state.currentChannel = "General";
    els.chatTitle.textContent = "Server";
    requestHistory("General");
    refreshChat();
}

function switchToDm(selectedUser = "") {
    const target = (selectedUser || els.dmUser.value).trim().toLowerCase();
    if (!target || target === state.username) return;

    state.currentChannel = normalizeDmChannel(state.username, target);
    els.chatTitle.textContent = `DM: ${capitalizeName(target)}`;
    els.dmUser.value = "";
    requestHistory(state.currentChannel);
    refreshChat();
}

els.login.addEventListener("click", () => connect("login"));
els.create.addEventListener("click", () => connect("create"));
els.send.addEventListener("click", sendMessage);
els.emojiButton.addEventListener("click", toggleEmojiPicker);
els.fileButton.addEventListener("click", sendFile);
els.serverButton.addEventListener("click", switchToServer);
els.dm.addEventListener("click", switchToDm);
els.logout.addEventListener("click", () => {
    state.intentionallyClosed = true;
    state.loggedIn = false;
    state.socket?.close();
    window.location.reload();
});

els.password.addEventListener("keydown", event => {
    if (event.key === "Enter") connect("login");
});

els.message.addEventListener("keydown", event => {
    sendTyping();
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

els.dmUser.addEventListener("keydown", event => {
    if (event.key === "Enter") switchToDm();
});

document.addEventListener("click", event => {
    if (!els.emojiPicker.hidden && !els.emojiPicker.contains(event.target) && event.target !== els.emojiButton) {
        els.emojiPicker.hidden = true;
    }
});

renderEmojiPicker();
