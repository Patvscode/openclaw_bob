document.addEventListener('DOMContentLoaded', () => {
  const socket = io();
  const form = document.getElementById('chat-form');
  const input = document.getElementById('msg-input');
  const messages = document.getElementById('messages');

  // Helper to add a message to the list
  const addMessage = (msg, isSelf) => {
    const li = document.createElement('li');
    li.textContent = msg;
    li.className = isSelf ? 'self' : 'other';
    messages.appendChild(li);
    messages.scrollTop = messages.scrollHeight;
  };

  // Receive broadcasted messages
  socket.on('chat message', (msg) => {
    // If the message originated from this client, it will already be displayed
    // We'll just display it for everyone (including self) for simplicity.
    addMessage(msg, false);
  });

  // Send a message
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = input.value.trim();
    if (msg === '') return;
    socket.emit('chat message', msg);
    addMessage(msg, true);
    input.value = '';
    input.focus();
  });
});
