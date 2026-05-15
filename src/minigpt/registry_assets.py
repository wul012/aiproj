from __future__ import annotations


def registry_style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --green:#047857; --amber:#b45309; }
* { box-sizing: border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.toolbar { display:grid; grid-template-columns:minmax(220px, 1fr) 150px 150px 74px 90px 82px 72px 120px; gap:10px; align-items:end; padding:14px 32px 0; }
.toolbar label { display:flex; flex-direction:column; gap:5px; color:var(--muted); font-size:12px; text-transform:uppercase; }
.toolbar input, .toolbar select, .toolbar button, .toolbar output { width:100%; min-height:38px; border:1px solid var(--line); border-radius:8px; background:#fff; color:var(--ink); font:inherit; }
.toolbar input, .toolbar select { padding:7px 9px; }
.toolbar button { cursor:pointer; font-weight:700; }
.toolbar button:active { transform:translateY(1px); }
.toolbar output { display:flex; align-items:center; justify-content:center; color:var(--muted); }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:1040px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
a { color:var(--blue); font-weight:700; text-decoration:none; margin-right:8px; }
.tag { display:inline-block; margin:0 4px 4px 0; padding:2px 6px; border-radius:999px; background:#e0f2fe; color:#075985; font-size:12px; font-weight:700; }
.pill { display:inline-block; min-width:58px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:#b91c1c; }
.pill.missing { background:#6b7280; }
.leaderboard { margin:0; padding-left:24px; }
.leaderboard li { padding:8px 0; border-bottom:1px solid var(--line); }
.leaderboard li:last-child { border-bottom:0; }
.leaderboard strong { display:inline-block; min-width:160px; }
.leaderboard span { color:var(--muted); }
pre { margin:0; white-space:pre-wrap; background:#f3f4f6; padding:12px; border-radius:8px; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats, .toolbar { padding-left:16px; padding-right:16px; } .toolbar { grid-template-columns:1fr 1fr; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def registry_script() -> str:
    return """<script>
(() => {
  const rows = Array.from(document.querySelectorAll("[data-run-row]"));
  const search = document.getElementById("registry-search");
  const quality = document.getElementById("quality-filter");
  const sortKey = document.getElementById("sort-key");
  const direction = document.getElementById("sort-direction");
  const count = document.getElementById("registry-count");
  const share = document.getElementById("share-view");
  const exportCsv = document.getElementById("export-visible-csv");
  const status = document.getElementById("registry-status");
  const numericKeys = new Set(["rank", "bestVal", "delta", "params", "artifacts", "rubric", "pair", "readiness", "eval"]);
  let ascending = true;

  const hasOption = (select, value) => Array.from(select.options).some((option) => option.value === value);

  const readState = () => {
    const params = new URLSearchParams(window.location.hash.slice(1));
    search.value = params.get("q") || "";
    const wantedQuality = params.get("quality") || "";
    if (hasOption(quality, wantedQuality)) quality.value = wantedQuality;
    const wantedSort = params.get("sort") || "rank";
    if (hasOption(sortKey, wantedSort)) sortKey.value = wantedSort;
    ascending = params.get("dir") !== "desc";
    direction.textContent = ascending ? "Asc" : "Desc";
    direction.setAttribute("aria-pressed", String(!ascending));
  };

  const writeState = () => {
    const params = new URLSearchParams();
    const query = (search.value || "").trim();
    if (query) params.set("q", query);
    if (quality.value) params.set("quality", quality.value);
    if (sortKey.value !== "rank") params.set("sort", sortKey.value);
    if (!ascending) params.set("dir", "desc");
    const next = params.toString();
    const base = window.location.href.split("#")[0];
    try {
      window.history.replaceState(null, "", next ? `${base}#${next}` : base);
    } catch {
      if (window.location.hash.slice(1) !== next) window.location.hash = next;
    }
  };

  const numberCompare = (a, b, key) => {
    const av = a.dataset[key] || "";
    const bv = b.dataset[key] || "";
    if (!av && !bv) return 0;
    if (!av) return 1;
    if (!bv) return -1;
    const delta = Number(av) - Number(bv);
    return ascending ? delta : -delta;
  };

  const textCompare = (a, b, key) => {
    const delta = (a.dataset[key] || "").localeCompare(b.dataset[key] || "", undefined, { numeric: true });
    return ascending ? delta : -delta;
  };

  const apply = () => {
    const query = (search.value || "").trim().toLowerCase();
    const wantedQuality = quality.value;
    const visible = [];
    rows.forEach((row) => {
      const matchesQuery = !query || (row.dataset.search || "").includes(query);
      const matchesQuality = !wantedQuality || row.dataset.quality === wantedQuality;
      const shown = matchesQuery && matchesQuality;
      row.hidden = !shown;
      if (shown) visible.push(row);
    });
    const key = sortKey.value;
    visible
      .sort((a, b) => numericKeys.has(key) ? numberCompare(a, b, key) : textCompare(a, b, key))
      .forEach((row) => row.parentElement.appendChild(row));
    count.value = `${visible.length} / ${rows.length}`;
    writeState();
    return visible;
  };

  const csvCell = (value) => `"${String(value).replace(/"/g, '""')}"`;

  const exportVisibleRows = () => {
    const headers = Array.from(document.querySelectorAll("#registry-table thead th")).map((cell) => cell.textContent.trim());
    const visible = rows.filter((row) => !row.hidden);
    const records = visible.map((row) => Array.from(row.cells).map((cell) => (cell.innerText || cell.textContent).replace(/\\s+/g, " ").trim()));
    const csv = [headers, ...records].map((record) => record.map(csvCell).join(",")).join("\\n");
    const blob = new Blob(["\\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `registry-visible-${visible.length}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    status.value = `CSV ${visible.length}`;
  };

  const shareCurrentView = async () => {
    writeState();
    try {
      await navigator.clipboard.writeText(window.location.href);
      status.value = "Link copied";
    } catch {
      status.value = "Link in URL";
    }
  };

  readState();
  search.addEventListener("input", apply);
  quality.addEventListener("change", apply);
  sortKey.addEventListener("change", apply);
  direction.addEventListener("click", () => {
    ascending = !ascending;
    direction.textContent = ascending ? "Asc" : "Desc";
    direction.setAttribute("aria-pressed", String(!ascending));
    apply();
  });
  share.addEventListener("click", shareCurrentView);
  exportCsv.addEventListener("click", exportVisibleRows);
  apply();
})();
</script>"""
