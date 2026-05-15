from __future__ import annotations

import json
from typing import Any


def playground_script(page_data: dict[str, Any]) -> str:
    data = json.dumps(page_data, ensure_ascii=False)
    return f"""<script>
const MiniGPTPlayground = {data};
function quoteArg(value) {{
  const text = String(value).replaceAll("'", "''");
  return "'" + text + "'";
}}
function checkpointOptionById(id) {{
  if (!id) return null;
  return (MiniGPTPlayground.checkpoints || []).find((item) => item.id === id) || null;
}}
function selectedCheckpointOption(selectId = 'checkpointSelect') {{
  const select = document.getElementById(selectId);
  if (!select || !select.value) return null;
  return checkpointOptionById(select.value);
}}
function formatValue(value) {{
  if (value === null || value === undefined || value === '') return 'missing';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  return String(value);
}}
function formatBytes(value) {{
  if (typeof value !== 'number') return 'missing';
  return value.toLocaleString() + ' B';
}}
function formatDelta(value) {{
  if (typeof value !== 'number') return 'missing';
  if (value === 0) return '0';
  return (value > 0 ? '+' : '') + value.toLocaleString();
}}
function formatSeconds(value) {{
  if (typeof value !== 'number') return 'missing';
  return value.toFixed(3) + 's';
}}
function formatTimestamp(value) {{
  if (!value) return 'missing';
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return String(value);
  return new Date(parsed).toLocaleString();
}}
function buildQuery(params) {{
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {{
    if (value !== null && value !== undefined && String(value).trim() !== '') {{
      query.set(key, String(value).trim());
    }}
  }}
  return query.toString();
}}
function appendCell(row, value) {{
  const cell = document.createElement('td');
  cell.textContent = formatValue(value);
  row.appendChild(cell);
  return cell;
}}
function setCheckpointSelect(selectId, id) {{
  const select = document.getElementById(selectId);
  if (select) select.value = id;
}}
function selectCheckpoint(id) {{
  setCheckpointSelect('checkpointSelect', id);
  setCheckpointSelect('pairLeftCheckpointSelect', id);
  buildCommands();
  renderCheckpointComparison();
}}
function buildCommands() {{
  const prompt = document.getElementById('promptInput').value || MiniGPTPlayground.defaults.prompt;
  const maxTokens = document.getElementById('maxTokensInput').value || MiniGPTPlayground.defaults.max_new_tokens;
  const temperature = document.getElementById('temperatureInput').value || MiniGPTPlayground.defaults.temperature;
  const topK = document.getElementById('topKInput').value || MiniGPTPlayground.defaults.top_k;
  const seed = document.getElementById('seedInput').value || MiniGPTPlayground.defaults.seed;
  const option = selectedCheckpointOption();
  const checkpoint = option ? option.path : MiniGPTPlayground.runDir + '/checkpoint.pt';
  const generate = `python scripts/generate.py --checkpoint ${{quoteArg(checkpoint)}} --prompt ${{quoteArg(prompt)}} --max-new-tokens ${{maxTokens}} --temperature ${{temperature}} --top-k ${{topK}}`;
  const chat = `python scripts/chat.py --checkpoint ${{quoteArg(checkpoint)}} --message ${{quoteArg(prompt)}} --max-new-tokens ${{maxTokens}} --temperature ${{temperature}} --top-k ${{topK}}`;
  const sample = `python scripts/sample_lab.py --checkpoint ${{quoteArg(checkpoint)}} --prompt ${{quoteArg(prompt)}} --max-new-tokens ${{maxTokens}} --case conservative:0.6:10:${{seed}} --case balanced:${{temperature}}:${{topK}}:${{Number(seed) + 1}} --case creative:1.1:0:${{Number(seed) + 2}}`;
  document.getElementById('generateCommand').textContent = generate;
  document.getElementById('chatCommand').textContent = chat;
  document.getElementById('sampleCommand').textContent = sample;
}}
async function loadCheckpoints() {{
  const select = document.getElementById('checkpointSelect');
  const status = document.getElementById('checkpointStatus');
  if (!select || !status) return;
  try {{
    const response = await fetch('/api/checkpoints');
    if (!response.ok) throw new Error('checkpoint endpoint unavailable');
    const data = await response.json();
    MiniGPTPlayground.checkpoints = Array.isArray(data.checkpoints) ? data.checkpoints : [];
    populateCheckpointSelect(select, data.default_checkpoint_id, 0);
    populateCheckpointSelect(document.getElementById('pairLeftCheckpointSelect'), data.default_checkpoint_id, 0);
    populateCheckpointSelect(document.getElementById('pairRightCheckpointSelect'), data.default_checkpoint_id, 1);
    if (data.default_checkpoint_id) select.value = data.default_checkpoint_id;
    status.textContent = `${{MiniGPTPlayground.checkpoints.length}} checkpoint option(s)`;
    select.disabled = MiniGPTPlayground.checkpoints.length === 0;
    buildCommands();
    renderCheckpointComparison();
  }} catch (error) {{
    MiniGPTPlayground.checkpoints = [];
    status.textContent = 'Start scripts/serve_playground.py for checkpoint selection.';
    select.disabled = true;
  }}
}}
function populateCheckpointSelect(select, defaultId, preferredIndex) {{
  if (!select) return;
  const previous = select.value;
  const options = MiniGPTPlayground.checkpoints || [];
  select.innerHTML = '';
  for (const item of options) {{
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = `${{item.id}}${{item.is_default ? ' (default)' : ''}}`;
    option.disabled = !item.exists;
    select.appendChild(option);
  }}
  const fallback = options[Math.min(preferredIndex, Math.max(options.length - 1, 0))];
  select.value = previous && checkpointOptionById(previous) ? previous : (fallback ? fallback.id : defaultId || '');
  select.disabled = options.length === 0;
}}
function renderCheckpointComparison() {{
  const body = document.getElementById('checkpointCompareBody');
  const status = document.getElementById('checkpointCompareStatus');
  if (!body || !status) return;
  const rows = MiniGPTPlayground.checkpointComparison || [];
  body.innerHTML = '';
  if (!rows.length) {{
    status.textContent = 'Start scripts/serve_playground.py for checkpoint comparison.';
    return;
  }}
  const selected = selectedCheckpointOption();
  for (const item of rows) {{
    const row = document.createElement('tr');
    if (selected && item.id === selected.id) row.className = 'selected-row';
    appendCell(row, `${{item.id}}${{item.is_default ? ' (default)' : ''}}`);
    appendCell(row, item.status);
    appendCell(row, formatBytes(item.size_bytes));
    appendCell(row, item.parameter_count);
    appendCell(row, item.dataset_version);
    appendCell(row, formatDelta(item.parameter_delta));
    appendCell(row, formatDelta(item.size_delta_bytes));
    const actions = document.createElement('td');
    const actionWrap = document.createElement('div');
    actionWrap.className = 'row-actions';
    const useButton = document.createElement('button');
    useButton.type = 'button';
    useButton.textContent = 'Use';
    useButton.disabled = !item.exists;
    useButton.addEventListener('click', () => selectCheckpoint(item.id));
    const infoLink = document.createElement('a');
    infoLink.href = item.model_info_endpoint || `/api/model-info?checkpoint=${{encodeURIComponent(item.id)}}`;
    infoLink.textContent = 'Model info';
    actionWrap.appendChild(useButton);
    actionWrap.appendChild(infoLink);
    actions.appendChild(actionWrap);
    row.appendChild(actions);
    body.appendChild(row);
  }}
}}
async function loadCheckpointComparison() {{
  const status = document.getElementById('checkpointCompareStatus');
  try {{
    const response = await fetch('/api/checkpoint-compare');
    if (!response.ok) throw new Error('checkpoint comparison endpoint unavailable');
    const data = await response.json();
    MiniGPTPlayground.checkpointComparison = Array.isArray(data.checkpoints) ? data.checkpoints : [];
    const summary = data.summary || {{}};
    if (status) status.textContent = `${{formatValue(summary.ready_count)}} ready / ${{formatValue(data.checkpoint_count)}} checkpoint option(s)`;
    renderCheckpointComparison();
  }} catch (error) {{
    MiniGPTPlayground.checkpointComparison = [];
    if (status) status.textContent = 'Start scripts/serve_playground.py for checkpoint comparison.';
    renderCheckpointComparison();
  }}
}}
function requestCheckpointLabel(item) {{
  return item.checkpoint_id || item.requested_checkpoint || item.left_checkpoint_id || item.requested_left_checkpoint || 'default';
}}
function requestOutputChars(item) {{
  if (typeof item.generated_chars === 'number') return item.generated_chars;
  if (typeof item.left_generated_chars === 'number' || typeof item.right_generated_chars === 'number') {{
    return `${{formatValue(item.left_generated_chars)}} / ${{formatValue(item.right_generated_chars)}}`;
  }}
  return 'missing';
}}
function requestStreamSummary(item) {{
  if (item.endpoint !== '/api/generate-stream') return 'n/a';
  const flags = [];
  if (item.stream_timed_out) flags.push('timeout');
  if (item.stream_cancelled) flags.push('cancelled');
  return `${{formatValue(item.stream_chunks)}} chunk(s)${{flags.length ? ' / ' + flags.join(', ') : ''}}`;
}}
function appendStatusCell(row, status) {{
  const cell = document.createElement('td');
  const badge = document.createElement('span');
  badge.className = 'status-pill ' + String(status || 'missing').replaceAll('_', '-');
  badge.textContent = formatValue(status);
  cell.appendChild(badge);
  row.appendChild(cell);
}}
function requestHistoryFilters() {{
  return {{
    status: document.getElementById('requestHistoryStatusFilter')?.value || '',
    endpoint: document.getElementById('requestHistoryEndpointFilter')?.value || '',
    checkpoint: document.getElementById('requestHistoryCheckpointFilter')?.value || '',
    limit: Number(document.getElementById('requestHistoryLimitInput')?.value || MiniGPTPlayground.requestHistoryFilters.limit || 12),
  }};
}}
function requestHistoryQuery(format) {{
  const filters = requestHistoryFilters();
  const query = buildQuery({{
    limit: filters.limit || 12,
    status: filters.status,
    endpoint: filters.endpoint,
    checkpoint: filters.checkpoint,
    format,
  }});
  return `/api/request-history?${{query}}`;
}}
function requestHistoryDetailUrl(logIndex) {{
  return `/api/request-history-detail?log_index=${{encodeURIComponent(logIndex)}}`;
}}
function updateRequestHistoryExportLink() {{
  const link = document.getElementById('requestHistoryExportLink');
  if (!link) return;
  link.href = requestHistoryQuery('csv');
}}
function setRequestHistoryDetail(text) {{
  const output = document.getElementById('requestHistoryDetailOutput');
  if (output) output.textContent = text;
}}
function renderRequestHistory() {{
  const body = document.getElementById('requestHistoryBody');
  const status = document.getElementById('requestHistoryStatus');
  if (!body || !status) return;
  const rows = MiniGPTPlayground.requestHistory || [];
  body.innerHTML = '';
  if (!rows.length) {{
    if (!status.textContent.startsWith('Start scripts/serve_playground.py')) {{
      status.textContent = 'No inference requests recorded yet.';
    }}
    return;
  }}
  for (const item of rows) {{
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
    if (logIndex) jsonLink.download = `request_history_${{logIndex}}.json`;
    actionWrap.appendChild(detailButton);
    actionWrap.appendChild(jsonLink);
    actions.appendChild(actionWrap);
    row.appendChild(actions);
    body.appendChild(row);
  }}
}}
async function showRequestHistoryDetail(logIndex) {{
  const status = document.getElementById('requestHistoryDetailStatus');
  if (!logIndex) {{
    if (status) status.textContent = 'Missing log_index for this request.';
    return;
  }}
  try {{
    if (status) status.textContent = `Loading request #${{logIndex}}`;
    const response = await fetch(requestHistoryDetailUrl(logIndex));
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'request history detail endpoint unavailable');
    MiniGPTPlayground.requestHistoryDetail = data;
    if (status) status.textContent = `Request #${{data.log_index}}`;
    setRequestHistoryDetail(JSON.stringify(data, null, 2));
  }} catch (error) {{
    MiniGPTPlayground.requestHistoryDetail = null;
    if (status) status.textContent = error.message || 'Start scripts/serve_playground.py for request history details.';
    setRequestHistoryDetail('');
  }}
}}
async function loadRequestHistory() {{
  const status = document.getElementById('requestHistoryStatus');
  try {{
    updateRequestHistoryExportLink();
    const response = await fetch(requestHistoryQuery());
    if (!response.ok) {{
      let message = 'request history endpoint unavailable';
      try {{
        const errorData = await response.json();
        message = errorData.error || message;
      }} catch (error) {{}}
      throw new Error(message);
    }}
    const data = await response.json();
    MiniGPTPlayground.requestHistory = Array.isArray(data.requests) ? data.requests : [];
    MiniGPTPlayground.requestHistoryFilters = data.filters || requestHistoryFilters();
    const summary = data.summary || {{}};
    if (status) {{
      status.textContent = `${{formatValue(data.record_count)}} shown / ${{formatValue(summary.matching_records)}} matched / ${{formatValue(summary.total_log_records)}} recorded`;
    }}
    renderRequestHistory();
  }} catch (error) {{
    MiniGPTPlayground.requestHistory = [];
    if (status) status.textContent = error.message || 'Start scripts/serve_playground.py for request history.';
    renderRequestHistory();
  }}
}}
async function generateLive() {{
  const output = document.getElementById('liveOutput');
  const generateButton = document.getElementById('liveGenerateButton');
  const stopButton = document.getElementById('liveStopButton');
  const checkpoint = selectedCheckpointOption();
  const payload = {{
    prompt: document.getElementById('promptInput').value || MiniGPTPlayground.defaults.prompt,
    max_new_tokens: Number(document.getElementById('maxTokensInput').value || MiniGPTPlayground.defaults.max_new_tokens),
    temperature: Number(document.getElementById('temperatureInput').value || MiniGPTPlayground.defaults.temperature),
    top_k: Number(document.getElementById('topKInput').value || MiniGPTPlayground.defaults.top_k),
    seed: Number(document.getElementById('seedInput').value || MiniGPTPlayground.defaults.seed),
  }};
  if (checkpoint) payload.checkpoint = checkpoint.id;
  if (MiniGPTPlayground.streamController) {{
    MiniGPTPlayground.streamController.abort();
  }}
  const controller = new AbortController();
  MiniGPTPlayground.streamController = controller;
  if (generateButton) generateButton.disabled = true;
  if (stopButton) stopButton.disabled = false;
  output.textContent = '';
  try {{
    const response = await fetch('/api/generate-stream', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload),
      signal: controller.signal,
    }});
    if (!response.ok) {{
      const data = await response.json();
      output.textContent = data.error || 'Generation failed';
      return;
    }}
    if (!response.body) {{
      output.textContent = 'Streaming response is unavailable in this browser.';
      return;
    }}
    await readGenerationStream(response, output);
  }} catch (error) {{
    if (error.name === 'AbortError') {{
      if (MiniGPTPlayground.streamController === controller) {{
        output.textContent = (output.textContent || '') + '\\n[stream cancelled]';
      }}
    }} else {{
      output.textContent = 'Start scripts/serve_playground.py to use live generation.';
    }}
  }} finally {{
    if (MiniGPTPlayground.streamController === controller) {{
      MiniGPTPlayground.streamController = null;
    }}
    if (generateButton) generateButton.disabled = false;
    if (stopButton) stopButton.disabled = true;
    setTimeout(loadRequestHistory, 200);
  }}
}}
function stopLiveGeneration() {{
  if (MiniGPTPlayground.streamController) {{
    MiniGPTPlayground.streamController.abort();
  }}
}}
async function readGenerationStream(response, output) {{
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let generated = '';
  while (true) {{
    const result = await reader.read();
    if (result.done) break;
    buffer += decoder.decode(result.value, {{stream: true}});
    const parts = buffer.split('\\n\\n');
    buffer = parts.pop() || '';
    for (const part of parts) {{
      const event = parseSseEvent(part);
      if (!event) continue;
      if (event.name === 'start') {{
        generated = event.data.prompt || '';
        output.textContent = generated;
      }} else if (event.name === 'token') {{
        generated = event.data.generated || (generated + (event.data.text || ''));
        output.textContent = generated;
      }} else if (event.name === 'end') {{
        const finalResponse = event.data.response || {{}};
        output.textContent = finalResponse.generated || generated;
      }} else if (event.name === 'timeout') {{
        const finalResponse = event.data.response || {{}};
        const partial = finalResponse.generated || generated;
        output.textContent = `${{partial}}\\n[stream timeout after ${{event.data.chunk_count}} chunk(s)]`;
      }} else if (event.name === 'error') {{
        output.textContent = event.data.error || 'Generation failed';
      }}
    }}
  }}
}}
function parseSseEvent(block) {{
  const lines = block.split('\\n');
  let name = 'message';
  const dataLines = [];
  for (const line of lines) {{
    if (line.startsWith('event:')) name = line.slice(6).trim();
    if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
  }}
  if (!dataLines.length) return null;
  try {{
    return {{name, data: JSON.parse(dataLines.join('\\n'))}};
  }} catch (error) {{
    return null;
  }}
}}
function renderPairArtifact(artifact) {{
  const status = document.getElementById('pairArtifactStatus');
  if (!status) return;
  status.textContent = '';
  if (!artifact || !artifact.html_href) {{
    return;
  }}
  const link = document.createElement('a');
  link.href = artifact.html_href;
  link.textContent = 'Open saved pair HTML';
  link.className = 'artifact-link';
  status.appendChild(link);
  const detail = document.createElement('span');
  detail.textContent = ' (' + (artifact.json_href || artifact.json_path || 'json saved') + ')';
  status.appendChild(detail);
}}
async function generatePairLive(saveArtifact = false) {{
  const leftOutput = document.getElementById('pairLeftOutput');
  const rightOutput = document.getElementById('pairRightOutput');
  const status = document.getElementById('pairGenerateStatus');
  const artifactStatus = document.getElementById('pairArtifactStatus');
  const left = selectedCheckpointOption('pairLeftCheckpointSelect');
  const right = selectedCheckpointOption('pairRightCheckpointSelect');
  const payload = {{
    prompt: document.getElementById('promptInput').value || MiniGPTPlayground.defaults.prompt,
    max_new_tokens: Number(document.getElementById('maxTokensInput').value || MiniGPTPlayground.defaults.max_new_tokens),
    temperature: Number(document.getElementById('temperatureInput').value || MiniGPTPlayground.defaults.temperature),
    top_k: Number(document.getElementById('topKInput').value || MiniGPTPlayground.defaults.top_k),
    seed: Number(document.getElementById('seedInput').value || MiniGPTPlayground.defaults.seed),
    left_checkpoint: left ? left.id : undefined,
    right_checkpoint: right ? right.id : undefined,
  }};
  leftOutput.textContent = 'Generating...';
  rightOutput.textContent = 'Generating...';
  status.textContent = saveArtifact ? 'Generating and saving pair...' : 'Generating pair...';
  if (artifactStatus) artifactStatus.textContent = '';
  try {{
    const endpoint = saveArtifact ? '/api/generate-pair-artifact' : '/api/generate-pair';
    const response = await fetch(endpoint, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload),
    }});
    const data = await response.json();
    if (!response.ok) {{
      leftOutput.textContent = data.error || 'Pair generation failed';
      rightOutput.textContent = data.error || 'Pair generation failed';
      status.textContent = 'failed';
      return;
    }}
    leftOutput.textContent = data.left?.generated || data.left?.continuation || '';
    rightOutput.textContent = data.right?.generated || data.right?.continuation || '';
    const comparison = data.comparison || {{}};
    status.textContent = `same output: ${{formatValue(comparison.generated_equal)}}; char delta: ${{formatDelta(comparison.generated_char_delta)}}`;
    renderPairArtifact(data.artifact);
  }} catch (error) {{
    leftOutput.textContent = 'Start scripts/serve_playground.py to use pair generation.';
    rightOutput.textContent = 'Start scripts/serve_playground.py to use pair generation.';
    status.textContent = 'unavailable';
  }} finally {{
    setTimeout(loadRequestHistory, 200);
  }}
}}
function copyCommand(id) {{
  navigator.clipboard.writeText(document.getElementById(id).textContent);
}}
window.addEventListener('DOMContentLoaded', () => {{
  for (const id of ['promptInput', 'maxTokensInput', 'temperatureInput', 'topKInput', 'seedInput']) {{
    document.getElementById(id).addEventListener('input', buildCommands);
  }}
  document.getElementById('checkpointSelect').addEventListener('change', () => {{
    buildCommands();
    renderCheckpointComparison();
  }});
  document.getElementById('liveGenerateButton').addEventListener('click', generateLive);
  document.getElementById('liveStopButton').addEventListener('click', stopLiveGeneration);
  document.getElementById('pairGenerateButton').addEventListener('click', () => generatePairLive(false));
  document.getElementById('pairSaveButton').addEventListener('click', () => generatePairLive(true));
  document.getElementById('pairLeftCheckpointSelect').addEventListener('change', renderCheckpointComparison);
  document.getElementById('pairRightCheckpointSelect').addEventListener('change', renderCheckpointComparison);
  document.getElementById('refreshCheckpointCompareButton').addEventListener('click', loadCheckpointComparison);
  document.getElementById('refreshRequestHistoryButton').addEventListener('click', loadRequestHistory);
  for (const id of ['requestHistoryStatusFilter', 'requestHistoryEndpointFilter', 'requestHistoryCheckpointFilter', 'requestHistoryLimitInput']) {{
    document.getElementById(id).addEventListener('input', () => {{
      updateRequestHistoryExportLink();
    }});
    document.getElementById(id).addEventListener('change', () => {{
      updateRequestHistoryExportLink();
    }});
  }}
  buildCommands();
  loadCheckpoints();
  loadCheckpointComparison();
  updateRequestHistoryExportLink();
  loadRequestHistory();
}});
</script>"""
