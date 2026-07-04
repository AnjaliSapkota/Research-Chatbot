const state = {
  files: [],
  messages: [],
  isTyping: false,
  documentId: null,
};

// DOM refercences
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

// File Upload

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

  uploadProgress.style.display = "block";
  progressBar.style.width = "20%";
  progressLabel.textContent = `Uploading ${file.name}...`;

  const formData = new FormData();
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(data => {

    progressBar.style.width = "100%";

    state.documentId = data.document_id;

    setTimeout(() => {

      uploadProgress.style.display = "none";

      addFileToState(file);

      addMessage(
        "ai",
        `📄 <strong>${data.filename}</strong> uploaded successfully.<br>
        Document indexed into ${data.chunks} chunks.`
      );

    }, 400);

  })
  .catch(err => {

    console.error(err);

    uploadProgress.style.display = "none";

    showToast("Upload failed", "error");

  });

}

function addFileToState(file) {

  const id = Date.now() + "-" + Math.random().toString(36).slice(2);

  state.files.push({
    id,
    name: file.name,
    file
  });

  renderFileList();

  showToast(`${file.name} uploaded successfully.`, "success");
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

  //  Messaging

async function ask() {

  const text = questionInput.value.trim();

  if (!text || state.isTyping) return;

  if (!state.documentId) {

    showToast("Upload a PDF first.", "error");
    return;

  }

  addMessage("user", escapeHtml(text));

  questionInput.value = "";

  autoResize();

  sendBtn.disabled = true;

  showTyping();

  try {

    const response = await fetch("/ask", {

      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({

        document_id: state.documentId,

        question: text

      })

    });

const data = await response.json();

hideTyping();

let html = `<div>${escapeHtml(data.answer)}</div>`;

if (data.sources && data.sources.length > 0) {

    html += "<hr>";
    html += "<b>Sources used:</b>";

    data.sources.forEach((chunk, i) => {

        html += `
            <div class="citation" style="
                margin-top:10px;
                padding:10px;
                border-left:4px solid #4f46e5;
                background:#f5f5f5;
                border-radius:6px;
            ">
                <b>Chunk ${i + 1}</b><br>
                ${escapeHtml(chunk)}
            </div>
        `;

    });

}

addMessage("ai", html);

  }

  catch(error){

    hideTyping();

    console.error(error);

    addMessage("ai","Something went wrong.");

  }

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

  //  Input handling

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

  //  Helpers

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