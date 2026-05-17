// static/js/chat.js

const chatForm = document.querySelector('#chatForm');
const messageInput = document.querySelector('#messageInput');
const chatMessages = document.querySelector('.chat-messages');

if (chatForm) {
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = messageInput.value.trim();
    if (!msg) return;

    const newMsg = document.createElement('div');
    newMsg.classList.add('message', 'user');
    newMsg.innerText = msg;
    chatMessages.appendChild(newMsg);
    messageInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}
