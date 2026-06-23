const state = {
  files: [],
  messages: [],
  isTyping: false,
};

/* ── DOM refs ── */
const chatMessages  = document.getElementById('chatMessages');
const questionInput = document.getElementById('question');
const sendBtn       = document.getElementById('sendBtn');
const fileUpload    = document.getElementById('fileUpload');
const uploadZone    = document.getElementById('uploadZone');
const fileList      = document.getElementById('fileList');
const uploadProgress = document.getElementById('uploadProgress');
const progressBar   = document.getElementById('progressBar');
const progressLabel = document.getElementById('progressLabel');
const emptyState    = document.getElementById('emptyState');

/* ─────────────────────────────────────────────
   File Upload
   ───────────────────────────────────────────── */

function upload() {
  fileUpload.click();
}

fileUpload.addEventListener('change', e => {
  const files = Array.from(e.target.files);
  files.forEach(processFile);
  fileUpload.value = '';
});

/* Drag & drop */
uploadZone.addEventListener('dragover', e => {
  e.preventDefault();
  uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
  if (files.length === 0) { showToast('Only PDF files are supported.', 'error'); return; }
  files.forEach(processFile);
});

uploadZone.addEventListener('click', upload);

function processFile(file) {
  if (file.type !== 'application/pdf') {
    showToast(`${file.name} is not a PDF.`, 'error');
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    showToast('File must be under 50 MB.', 'error');
    return;
  }
  if (state.files.find(f => f.name === file.name)) {
    showToast(`${file.name} is already loaded.`, 'error');
    return;
  }

  simulateUpload(file);
}

function simulateUpload(file) {
  uploadProgress.style.display = 'block';
  progressBar.style.width = '0%';
  progressLabel.textContent = `Uploading ${file.name}…`;

  let pct = 0;
  const iv = setInterval(() => {
    pct += Math.random() * 22;
    if (pct >= 100) {
      pct = 100;
      clearInterval(iv);
      setTimeout(() => {
        uploadProgress.style.display = 'none';
        addFileToState(file);
      }, 300);
    }
    progressBar.style.width = `${Math.min(pct, 100)}%`;
  }, 120);
}

function addFileToState(file) {
  const id = Date.now() + '-' + Math.random().toString(36).slice(2);
  state.files.push({ id, name: file.name, file });
  renderFileList();
  showToast(`${file.name} ready.`, 'success');

  /* Add a system message into chat */
  addMessage('ai', `📄 <strong>${file.name}</strong> has been loaded. You can now ask questions about its contents.`);
}

function renderFileList() {
  fileList.innerHTML = '';
  state.files.forEach(f => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
      <span class="file-icon">📄</span>
      <span class="file-name" title="${f.name}">${f.name}</span>
      <button class="file-remove" title="Remove" onclick="removeFile('${f.id}')">✕</button>
    `;
    fileList.appendChild(item);
  });
}

function removeFile(id) {
  const f = state.files.find(f => f.id === id);
  if (!f) return;
  state.files = state.files.filter(f => f.id !== id);
  renderFileList();
  showToast(`${f.name} removed.`);
}

/* ─────────────────────────────────────────────
   Messaging
   ───────────────────────────────────────────── */

function ask() {
  const text = questionInput.value.trim();
  if (!text || state.isTyping) return;

  if (state.files.length === 0) {
    showToast('Upload a PDF first so I have context to search.', 'error');
    questionInput.focus();
    return;
  }

  addMessage('user', escapeHtml(text));
  questionInput.value = '';
  autoResize();
  sendBtn.disabled = true;

  showEmptyState(false);
  simulateAIResponse(text);
}

function addMessage(role, html) {
  state.messages.push({ role, html });

  /* Remove empty state once first real message appears */
  if (emptyState) showEmptyState(false);

  const row = document.createElement('div');
  row.className = `message-row ${role === 'user' ? 'user' : ''}`;

  const now = new Date();
  const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (role === 'ai') {
    row.innerHTML = `
      <div class="avatar ai">AI</div>
      <div class="message-content">
        <div class="message-meta">Research Assistant · ${time}</div>
        <div class="bubble ai-bubble">${html}</div>
      </div>`;
  } else {
    row.innerHTML = `
      <div class="avatar user-av">You</div>
      <div class="message-content">
        <div class="message-meta">${time}</div>
        <div class="bubble user-bubble">${html}</div>
      </div>`;
  }

  chatMessages.appendChild(row);
  scrollToBottom();
}

/* Typing indicator */
function showTyping() {
  state.isTyping = true;
  const row = document.createElement('div');
  row.className = 'message-row';
  row.id = 'typingRow';
  row.innerHTML = `
    <div class="avatar ai">AI</div>
    <div class="message-content">
      <div class="bubble ai-bubble" style="padding: 10px 16px;">
        <div class="typing-dots"><span></span><span></span><span></span></div>
      </div>
    </div>`;
  chatMessages.appendChild(row);
  scrollToBottom();
}

function hideTyping() {
  const row = document.getElementById('typingRow');
  if (row) row.remove();
  state.isTyping = false;
  sendBtn.disabled = false;
}

/* ─────────────────────────────────────────────
   Simulated AI response
   (Replace this block with your real API call)
   ───────────────────────────────────────────── */

const MOCK_RESPONSES = [
  q => `Based on the uploaded document${state.files.length > 1 ? 's' : ''}, here's what I found regarding <em>"${q}"</em>:\n\nThe text discusses this concept in the context of the broader argument presented in the paper. Key points include a multi-step analysis of the underlying mechanisms and comparative data from related studies.\n\n<span class="citation">§ 2.1 — p. 4</span> <span class="citation">§ 4.3 — p. 11</span>`,
  q => `Great question about <em>"${q}"</em>. The document references several supporting data points:\n\n1. The methodology section outlines a controlled experimental design.\n2. Results indicate a statistically significant correlation.\n3. The authors note limitations in sample size.\n\n<span class="citation">Table 3 — p. 8</span>`,
  q => `Searching through the loaded PDF${state.files.length > 1 ? 's' : ''} for <em>"${q}"</em>…\n\nI found a relevant passage in the introduction that directly addresses this. The authors frame the problem using prior literature and propose a novel framework to resolve existing gaps in the field.\n\n<span class="citation">Introduction — p. 2</span> <span class="citation">Discussion — p. 14</span>`,
];

function simulateAIResponse(query) {
  showTyping();
  const delay = 1200 + Math.random() * 1000;

  setTimeout(() => {
    hideTyping();
    const pick = MOCK_RESPONSES[Math.floor(Math.random() * MOCK_RESPONSES.length)];
    addMessage('ai', pick(escapeHtml(query)));
  }, delay);
}

/* ─────────────────────────────────────────────
   Suggestion chips
   ───────────────────────────────────────────── */

document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    questionInput.value = chip.textContent;
    autoResize();
    questionInput.focus();
  });
});

/* ─────────────────────────────────────────────
   Input handling
   ───────────────────────────────────────────── */

questionInput.addEventListener('input', autoResize);
questionInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    ask();
  }
});

function autoResize() {
  questionInput.style.height = 'auto';
  questionInput.style.height = Math.min(questionInput.scrollHeight, 140) + 'px';

  const hasText = questionInput.value.trim().length > 0;
  sendBtn.disabled = !hasText || state.isTyping;
}

/* ─────────────────────────────────────────────
   Helpers
   ───────────────────────────────────────────── */

function scrollToBottom() {
  requestAnimationFrame(() => {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

function showEmptyState(show) {
  if (emptyState) emptyState.style.display = show ? 'block' : 'none';
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

let toastTimeout;
function showToast(msg, type = '') {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className = `toast ${type}`;
  void toast.offsetWidth;
  toast.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove('show'), 3200);
}

/* Initialise */
sendBtn.disabled = true;