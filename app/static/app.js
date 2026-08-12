let mode = "text";

function switchTab(target) {
  mode = target;
  document.getElementById('tabText').classList.toggle('active', target === 'text');
  document.getElementById('tabFile').classList.toggle('active', target === 'file');
  document.getElementById('tabClassify').classList.toggle('active', target === 'classify');
  document.getElementById('tabHistory').classList.toggle('active', target === 'history');
  document.getElementById('textPanel').classList.toggle('hidden', target !== 'text');
  document.getElementById('filePanel').classList.toggle('hidden', target !== 'file');
  document.getElementById('classifyPanel').classList.toggle('hidden', target !== 'classify');
  document.getElementById('historyPanel').classList.toggle('hidden', target !== 'history');
  document.getElementById('submitBtn').classList.toggle('hidden', target !== 'text' && target !== 'file');
  document.getElementById('classifyBtn').classList.toggle('hidden', target !== 'classify');
  document.getElementById('resultBox').classList.add('hidden');
  document.getElementById('classifyResultBox').classList.add('hidden');
  document.getElementById('errorBox').classList.add('hidden');

  if (target === 'history') {
    loadHistory();
  }
}

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');

dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('drag');
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    updateFileName();
  }
});
fileInput.addEventListener('change', updateFileName);

function updateFileName() {
  const f = fileInput.files[0];
  document.getElementById('fileName').textContent = f ? `Selected: ${f.name}` : "";
}

async function doSummarize() {
  const btn = document.getElementById('submitBtn');
  const errorBox = document.getElementById('errorBox');
  const resultBox = document.getElementById('resultBox');
  const maxWords = document.getElementById('maxWords').value;

  errorBox.classList.add('hidden');
  resultBox.classList.add('hidden');

  let url, options;

  if (mode === "text") {
    const text = document.getElementById('textInput').value.trim();
    if (!text) { showError("Please paste some text first."); return; }
    url = "/summarize";
    options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, max_words: parseInt(maxWords) })
    };
  } else {
    const file = fileInput.files[0];
    if (!file) { showError("Please choose a file first."); return; }
    const formData = new FormData();
    formData.append("file", file);
    formData.append("max_words", maxWords);
    url = "/summarize/file";
    options = { method: "POST", body: formData };
  }

  btn.disabled = true;
  btn.textContent = "Summarizing...";

  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
      showError(typeof data.detail === "string" ? data.detail : "Something went wrong.");
      return;
    }

    document.getElementById('summaryText').textContent = data.summary;
    document.getElementById('metaText').textContent =
      `${data.original_length_words} words → ${data.summary_length_words} words`;
    resultBox.classList.remove('hidden');
  } catch (err) {
    showError("Could not reach the server. Is it still running?");
  } finally {
    btn.disabled = false;
    btn.textContent = "Summarize";
  }
}

async function doClassify() {
  const btn = document.getElementById('classifyBtn');
  const errorBox = document.getElementById('errorBox');
  const resultBox = document.getElementById('classifyResultBox');
  const text = document.getElementById('classifyInput').value.trim();

  errorBox.classList.add('hidden');
  resultBox.classList.add('hidden');

  if (!text) { showError("Please paste a message first."); return; }

  btn.disabled = true;
  btn.textContent = "Classifying...";

  try {
    const response = await fetch("/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    });
    const data = await response.json();

    if (!response.ok) {
      showError(typeof data.detail === "string" ? data.detail : "Something went wrong.");
      return;
    }

    document.getElementById('classifyText').textContent =
      `Intent: ${data.intent}\nPriority: ${data.priority}\nSentiment: ${data.sentiment}\nRequires human: ${data.requires_human}`;
    resultBox.classList.remove('hidden');
  } catch (err) {
    showError("Could not reach the server. Is it still running?");
  } finally {
    btn.disabled = false;
    btn.textContent = "Classify";
  }
}

function showError(msg) {
  const errorBox = document.getElementById('errorBox');
  errorBox.textContent = msg;
  errorBox.classList.remove('hidden');
}

async function loadHistory() {
  const listEl = document.getElementById('historyList');
  const countEl = document.getElementById('historyCount');
  listEl.innerHTML = '<div class="historyEmpty">Loading...</div>';

  try {
    const response = await fetch('/history?limit=20');
    const records = await response.json();

    if (!records.length) {
      listEl.innerHTML = '<div class="historyEmpty">No requests yet. Try Summarize or Classify.</div>';
      countEl.textContent = '';
      return;
    }

    countEl.textContent = `${records.length} recent request${records.length > 1 ? 's' : ''}`;
    listEl.innerHTML = records.map(renderHistoryCard).join('');
  } catch (err) {
    listEl.innerHTML = '<div class="historyEmpty">Could not load history.</div>';
  }
}

function renderHistoryCard(record) {
  const time = new Date(record.created_at).toLocaleString();
  const isClassify = record.request_type === 'classify';
  const badgeClass = isClassify ? 'badge-classify' : 'badge-summarize';
  const badgeLabel = isClassify ? 'Classify' : 'Summarize';

  let output;
  try {
    output = JSON.parse(record.output);
  } catch (e) {
    output = null;
  }

  const inputPreview = record.input_text.length > 160
    ? record.input_text.slice(0, 160) + '...'
    : record.input_text;

  let outputHtml;
  let pillsHtml = '';

  if (isClassify && output) {
    outputHtml = `Intent: ${escapeHtml(output.intent)} · Sentiment: ${escapeHtml(output.sentiment)}`;
    const pills = [];
    pills.push(`<span class="pill ${output.priority === 'high' ? 'high' : ''}">${escapeHtml(output.priority)} priority</span>`);
    if (output.confidence !== undefined) {
      pills.push(`<span class="pill">confidence ${Math.round(output.confidence * 100)}%</span>`);
    }
    if (output.requires_human) {
      pills.push(`<span class="pill review">needs human review</span>`);
    }
    pillsHtml = `<div class="pillRow">${pills.join('')}</div>`;
  } else if (output) {
    outputHtml = escapeHtml(output.summary || '');
  } else {
    outputHtml = '(could not parse result)';
  }

  return `
    <div class="historyCard">
      <div class="historyHeader">
        <span class="historyBadge ${badgeClass}">${badgeLabel}</span>
        <span class="historyTime">${time}</span>
      </div>
      <div class="historyInput"><span class="label">Input:</span> ${escapeHtml(inputPreview)}</div>
      <div class="historyOutput"><span class="label">Result</span>${outputHtml}</div>
      ${pillsHtml}
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}