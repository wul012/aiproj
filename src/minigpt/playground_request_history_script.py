from __future__ import annotations


def playground_request_history_script() -> str:
    return r"""
function requestCheckpointLabel(item) {
  return item.checkpoint_id || item.requested_checkpoint || item.left_checkpoint_id || item.requested_left_checkpoint || 'default';
}
function requestOutputChars(item) {
  if (typeof item.generated_chars === 'number') return item.generated_chars;
  if (typeof item.left_generated_chars === 'number' || typeof item.right_generated_chars === 'number') {
    return `${formatValue(item.left_generated_chars)} / ${formatValue(item.right_generated_chars)}`;
  }
  return 'missing';
}
function requestStreamSummary(item) {
  if (item.endpoint !== '/api/generate-stream') return 'n/a';
  const flags = [];
  if (item.stream_timed_out) flags.push('timeout');
  if (item.stream_cancelled) flags.push('cancelled');
  return `${formatValue(item.stream_chunks)} chunk(s)${flags.length ? ' / ' + flags.join(', ') : ''}`;
}
function appendStatusCell(row, status) {
  const cell = document.createElement('td');
  const badge = document.createElement('span');
  badge.className = 'status-pill ' + String(status || 'missing').replaceAll('_', '-');
  badge.textContent = formatValue(status);
  cell.appendChild(badge);
  row.appendChild(cell);
}
function requestHistoryFilters() {
  return {
    status: document.getElementById('requestHistoryStatusFilter')?.value || '',
    endpoint: document.getElementById('requestHistoryEndpointFilter')?.value || '',
    checkpoint: document.getElementById('requestHistoryCheckpointFilter')?.value || '',
    limit: Number(document.getElementById('requestHistoryLimitInput')?.value || MiniGPTPlayground.requestHistoryFilters.limit || 12),
  };
}
function requestHistoryQuery(format) {
  const filters = requestHistoryFilters();
  const query = buildQuery({
    limit: filters.limit || 12,
    status: filters.status,
    endpoint: filters.endpoint,
    checkpoint: filters.checkpoint,
    format,
  });
  return `/api/request-history?${query}`;
}
function requestHistoryDetailUrl(logIndex) {
  return `/api/request-history-detail?log_index=${encodeURIComponent(logIndex)}`;
}
function updateRequestHistoryExportLink() {
  const link = document.getElementById('requestHistoryExportLink');
  if (!link) return;
  link.href = requestHistoryQuery('csv');
}
function setRequestHistoryDetail(text) {
  const output = document.getElementById('requestHistoryDetailOutput');
  if (output) output.textContent = text;
}
function renderRequestHistory() {
  const body = document.getElementById('requestHistoryBody');
  const status = document.getElementById('requestHistoryStatus');
  if (!body || !status) return;
  const rows = MiniGPTPlayground.requestHistory || [];
  body.innerHTML = '';
  if (!rows.length) {
    if (!status.textContent.startsWith('Start scripts/serve_playground.py')) {
      status.textContent = 'No inference requests recorded yet.';
    }
    return;
  }
  for (const item of rows) {
    const row = document.createElement('tr');
    appendCell(row, item.log_index);
    appendCell(row, formatTimestamp(item.timestamp));
    appendCell(row, item.endpoint);
    appendStatusCell(row, item.status);
    appendCell(row, requestCheckpointLabel(item));
    appendCell(row, item.prompt_chars);
    appendCell(row, requestOutputChars(item));
    appendCell(row, requestStreamSummary(item));
    appendCell(row, formatSeconds(item.stream_elapsed_seconds));
    const actions = document.createElement('td');
    const actionWrap = document.createElement('div');
    actionWrap.className = 'row-actions';
    const logIndex = item.log_index;
    const detailButton = document.createElement('button');
    detailButton.type = 'button';
    detailButton.textContent = 'Details';
    detailButton.disabled = !logIndex;
    detailButton.addEventListener('click', () => showRequestHistoryDetail(logIndex));
    const jsonLink = document.createElement('a');
    jsonLink.textContent = 'JSON';
    jsonLink.href = logIndex ? requestHistoryDetailUrl(logIndex) : '#';
    if (logIndex) jsonLink.download = `request_history_${logIndex}.json`;
    actionWrap.appendChild(detailButton);
    actionWrap.appendChild(jsonLink);
    actions.appendChild(actionWrap);
    row.appendChild(actions);
    body.appendChild(row);
  }
}
async function showRequestHistoryDetail(logIndex) {
  const status = document.getElementById('requestHistoryDetailStatus');
  if (!logIndex) {
    if (status) status.textContent = 'Missing log_index for this request.';
    return;
  }
  try {
    if (status) status.textContent = `Loading request #${logIndex}`;
    const response = await fetch(requestHistoryDetailUrl(logIndex));
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'request history detail endpoint unavailable');
    MiniGPTPlayground.requestHistoryDetail = data;
    if (status) status.textContent = `Request #${data.log_index}`;
    setRequestHistoryDetail(JSON.stringify(data, null, 2));
  } catch (error) {
    MiniGPTPlayground.requestHistoryDetail = null;
    if (status) status.textContent = error.message || 'Start scripts/serve_playground.py for request history details.';
    setRequestHistoryDetail('');
  }
}
async function loadRequestHistory() {
  const status = document.getElementById('requestHistoryStatus');
  try {
    updateRequestHistoryExportLink();
    const response = await fetch(requestHistoryQuery());
    if (!response.ok) {
      let message = 'request history endpoint unavailable';
      try {
        const errorData = await response.json();
        message = errorData.error || message;
      } catch (error) {}
      throw new Error(message);
    }
    const data = await response.json();
    MiniGPTPlayground.requestHistory = Array.isArray(data.requests) ? data.requests : [];
    MiniGPTPlayground.requestHistoryFilters = data.filters || requestHistoryFilters();
    const summary = data.summary || {};
    if (status) {
      status.textContent = `${formatValue(data.record_count)} shown / ${formatValue(summary.matching_records)} matched / ${formatValue(summary.total_log_records)} recorded`;
    }
    renderRequestHistory();
  } catch (error) {
    MiniGPTPlayground.requestHistory = [];
    if (status) status.textContent = error.message || 'Start scripts/serve_playground.py for request history.';
    renderRequestHistory();
  }
}
"""


__all__ = ["playground_request_history_script"]
