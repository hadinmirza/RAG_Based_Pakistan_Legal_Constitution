const chatWindow = document.getElementById('chat-window');
const composer = document.getElementById('composer');
const input = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addMessage(text, role) {
  const wrap = document.createElement('div');
  wrap.className = `message ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  wrap.appendChild(bubble);
  chatWindow.appendChild(wrap);
  scrollToBottom();
  return wrap;
}

function addCitations(wrap, citations) {
  if (!citations || citations.length === 0) return;
  const bubble = wrap.querySelector('.bubble');
  const row = document.createElement('div');
  row.className = 'citations';
  citations.forEach(c => {
    const chip = document.createElement('span');
    chip.className = 'citation-chip';
    const label = c.article ? `Article ${c.article}` : (c.title || 'Source');
    chip.textContent = label;
    if (c.title) chip.title = c.title;
    row.appendChild(chip);
  });
  bubble.appendChild(row);
}

function showTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'message bot typing';
  wrap.id = 'typing-indicator';
  wrap.innerHTML = `<div class="bubble">
    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
  </div>`;
  chatWindow.appendChild(wrap);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

async function askQuestion(question) {
  showTyping();
  sendBtn.disabled = true;

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();
    hideTyping();

    if (!res.ok) {
      addMessage(data.error || 'Something went wrong. Please try again.', 'bot error');
      return;
    }

    if (data.status === 'rejected_prescope' || data.status === 'rejected_llm') {
      const wrap = addMessage(
        data.answer || "This question is outside the scope of the Constitution of Pakistan, so I can't answer it.",
        'bot system'
      );
      return;
    }

    const wrap = addMessage(data.answer || 'No answer returned.', 'bot');
    addCitations(wrap, data.citations);

  } catch (err) {
    hideTyping();
    addMessage('Could not reach the server. Is the Flask app running?', 'bot error');
  } finally {
    sendBtn.disabled = false;
  }
}

composer.addEventListener('submit', (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  addMessage(question, 'user');
  input.value = '';
  askQuestion(question);
});
