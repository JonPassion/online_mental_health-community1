function saveMessage(tab, msg) {
  const history = JSON.parse(localStorage.getItem(tab)) || [];
  history.push(msg);
  localStorage.setItem(tab, JSON.stringify(history));
}

function loadMessages(tab) {
  const chatWindow = document.getElementById(tab + 'Chat');
  const history = JSON.parse(localStorage.getItem(tab)) || [];
  chatWindow.innerHTML = history.map(
    m => `<div class="message ${m.type}">${m.text}</div>`
  ).join('');
}
