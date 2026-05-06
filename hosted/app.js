const state = {
    socket: null,
    username: "",
    currentChannel: "General",
    chatData: { General: [] },
};

const els = {
    username: document.getElementById("username"),
    password: document.getElementById("password"),
    status: document.getElementById("status-text"),
    server: document.getElementById("server-text"),
    login: document.getElementById("login-button"),
    create: document.getElementById("create-button"),
    loginSection: document.getElementById("login-section"),
    chatSection: document.getElementById("chat-section"),
    chatTitle: document.getElementById("chat-title"),
    history: document.getElementById("chat-history"),
    message: document.getElementById("message-input"),
    send: document.getElementById("send-button"),
    dmUser: document.getElementById("dm-user-input"),
    dm: document.getElementById("dm-button"),
    serverButton: document.getElementById("server-button"),
    logout: document.getElementById("logout-button"),
};

function getWebSocketUrl() {
    if (window.SECURECHAT_WS_URL) {
        return window.SECURECHAT_WS_URL;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/`;
}

function setStatus(message, isError = false) {
    els.status.textContent = message;
    els.status.classList.toggle("error", isError);
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

    div.innerHTML = `<b>${capitalizeName(escapeHtml(sender))}</b>: ${formatMessage(content)}`;
    return div;
}

function refreshChat() {
    const messages = state.chatData[state.currentChannel] || [];
    els.history.innerHTML = "";
    messages.forEach(message => els.history.appendChild(renderMessage(message)));
    els.history.scrollTop = els.history.scrollHeight;
}

function pushMessage(message) {
    const channel = message.channel || "General";
    if (!state.chatData[channel]) state.chatData[channel] = [];
    state.chatData[channel].push(message);
    if (channel === state.currentChannel) refreshChat();
}

function switchToChat() {
    els.loginSection.hidden = true;
    els.chatSection.hidden = false;
    state.currentChannel = "General";
    els.chatTitle.textContent = "Server";
    refreshChat();
}

function requestHistory(channel) {
    if (state.socket?.readyState === WebSocket.OPEN) {
        state.socket.send(JSON.stringify({ action: "get_history", channel }));
    }
}

function connect(action) {
    const username = els.username.value.trim().toLowerCase();
    const password = els.password.value;
    const url = getWebSocketUrl();

    if (!username || !password) {
        setStatus("Enter a username and password.", true);
        return;
    }

    setStatus("Connecting...");
    els.server.textContent = `WebSocket: ${url}`;
    state.username = username;

    const socket = new WebSocket(url);
    state.socket = socket;

    socket.addEventListener("open", () => {
        socket.send(JSON.stringify({ action, user_id: username, password, channel: "General" }));
    });

    socket.addEventListener("message", event => {
        const data = JSON.parse(event.data);

        if (data.status === "success") {
            if (action === "create") {
                setStatus("Account created. You can log in now.");
                socket.close();
                return;
            }

            setStatus(data.message || "Connected.");
            state.chatData.General = data.history || [];
            switchToChat();
            return;
        }

        if (data.status === "error") {
            setStatus(data.message || "Unable to connect.", true);
            socket.close();
            return;
        }

        if (data.action === "history_update") {
            state.chatData[data.channel || "General"] = data.history || [];
            refreshChat();
            return;
        }

        pushMessage(data);
    });

    socket.addEventListener("close", () => {
        if (!els.chatSection.hidden) {
            pushMessage({ sender: "SYSTEM", message: "Disconnected from server.", channel: state.currentChannel });
        }
    });

    socket.addEventListener("error", () => {
        setStatus("Could not connect to the WebSocket server.", true);
    });
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

function switchToServer() {
    state.currentChannel = "General";
    els.chatTitle.textContent = "Server";
    requestHistory("General");
    refreshChat();
}

function switchToDm() {
    const target = els.dmUser.value.trim().toLowerCase();
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
els.serverButton.addEventListener("click", switchToServer);
els.dm.addEventListener("click", switchToDm);
els.logout.addEventListener("click", () => {
    state.socket?.close();
    window.location.reload();
});

els.password.addEventListener("keydown", event => {
    if (event.key === "Enter") connect("login");
});

els.message.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

els.dmUser.addEventListener("keydown", event => {
    if (event.key === "Enter") switchToDm();
});

els.server.textContent = `WebSocket: ${getWebSocketUrl()}`;
