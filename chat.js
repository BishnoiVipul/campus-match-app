// chats.js - ONLY handles the Chat page logic
document.addEventListener('DOMContentLoaded', function() {
    const matchList = document.getElementById('match-list');
    const chatPlaceholder = document.getElementById('chat-placeholder');
    const conversationContainer = document.getElementById('conversation-container');
    const messageList = document.getElementById('message-list');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    
    let currentMatchId = null;
    const loggedInUserId = localStorage.getItem('userId');

    if (!loggedInUserId) return;

    fetch(`/matches?userId=${loggedInUserId}`)
        .then(response => response.json())
        .then(matches => {
            if (matches.length === 0) {
                matchList.innerHTML = '<p class="no-matches">No matches yet.</p>';
                return;
            }
            matches.forEach(match => {
                const matchElement = document.createElement('div');
                matchElement.className = 'chat-preview';
                matchElement.dataset.matchId = match.match_id;
                matchElement.dataset.userName = match.fullName;
                
                matchElement.innerHTML = `<div class="chat-avatar">${match.fullName.charAt(0)}</div><div class="chat-info"><h3>${match.fullName}</h3><p>Start chatting...</p></div>`;
                matchElement.addEventListener('click', () => loadConversation(match.match_id, match.fullName));
                matchList.appendChild(matchElement);
            });
        });

    function loadConversation(matchId, userName) {
        currentMatchId = matchId;
        chatPlaceholder.style.display = 'none';
        conversationContainer.style.display = 'flex';
        messageList.innerHTML = '';
        document.querySelectorAll('.chat-preview').forEach(el => el.classList.remove('active'));
        document.querySelector(`.chat-preview[data-match-id='${matchId}']`).classList.add('active');
        fetch(`/messages/${matchId}`)
            .then(response => response.json())
            .then(messages => {
                messages.forEach(msg => displayMessage(msg));
            });
    }

    function displayMessage(msg) {
        const msgElement = document.createElement('div');
        msgElement.className = 'message';
        msgElement.classList.add(msg.sender_id.toString() === loggedInUserId ? 'sent' : 'received');
        msgElement.textContent = msg.message_text;
        messageList.appendChild(msgElement);
        messageList.scrollTop = messageList.scrollHeight;
    }

    messageForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageText = messageInput.value.trim();
        if (messageText === '' || !currentMatchId) return;
        const messageData = { match_id: currentMatchId, sender_id: loggedInUserId, message_text: messageText };
        fetch('/send_message', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(messageData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayMessage(messageData);
                messageInput.value = '';
            }
        });
    });
});