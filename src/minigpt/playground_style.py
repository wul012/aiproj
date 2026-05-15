from __future__ import annotations


def playground_style() -> str:
    return """<style>
:root {
  color-scheme: light;
  --ink: #172033;
  --muted: #536176;
  --line: #d9e2ec;
  --panel: #ffffff;
  --page: #f5f7f4;
  --blue: #1d4ed8;
  --green: #047857;
  --amber: #b45309;
  --red: #b91c1c;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font-family: Arial, "Microsoft YaHei", sans-serif;
  line-height: 1.5;
}
header {
  padding: 24px 32px 16px;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
}
h1 { margin: 0 0 6px; font-size: 27px; letter-spacing: 0; }
h2 { margin: 26px 32px 12px; font-size: 18px; letter-spacing: 0; }
h3 { margin: 10px 0 5px; font-size: 15px; letter-spacing: 0; }
p { margin: 0; color: var(--muted); overflow-wrap: anywhere; }
button, input, output, select, textarea {
  font: inherit;
}
button {
  border: 1px solid #93a4b7;
  border-radius: 7px;
  background: #ffffff;
  color: var(--ink);
  padding: 8px 12px;
  cursor: pointer;
}
button:hover { border-color: var(--blue); color: var(--blue); }
textarea, input, select {
  width: 100%;
  border: 1px solid #b8c5d2;
  border-radius: 7px;
  padding: 9px 10px;
  background: #ffffff;
  color: var(--ink);
}
textarea { min-height: 96px; resize: vertical; }
output { color: var(--muted); }
.stats, .links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
  gap: 12px;
  padding: 18px 32px 0;
}
.stat, .link, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.stat { padding: 13px; min-height: 82px; }
.label { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.value { margin-top: 6px; font-size: 20px; font-weight: 700; overflow-wrap: anywhere; }
.panel { margin: 0 32px 18px; padding: 16px; }
.builder {
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(300px, 1.1fr);
  gap: 16px;
}
.controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.commands {
  display: grid;
  gap: 10px;
}
.command {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: start;
}
pre {
  margin: 0;
  min-height: 44px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #eef3f7;
  border-radius: 7px;
  padding: 10px;
}
.live-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
}
.live-actions label { min-width: 220px; }
.selected-row { background: #eef6ff; }
.row-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.row-actions a { color: var(--blue); font-weight: 700; text-decoration: none; }
.detail-panel {
  margin-top: 12px;
  display: grid;
  gap: 8px;
}
.detail-panel pre { min-height: 118px; }
.status-pill {
  display: inline-block;
  min-width: 58px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef3f7;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}
.status-pill.ok { background: #dcfce7; color: var(--green); }
.status-pill.timeout { background: #fef3c7; color: var(--amber); }
.status-pill.cancelled, .status-pill.error, .status-pill.bad-request { background: #fee2e2; color: var(--red); }
.pair-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(260px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.pair-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
  background: #ffffff;
}
.artifact-link { color: var(--blue); font-weight: 700; text-decoration: none; }
.output {
  margin-top: 12px;
  min-height: 92px;
}
.links { padding-top: 0; }
.link { padding: 12px; min-height: 105px; }
.link a { color: var(--blue); font-weight: 700; text-decoration: none; }
.link.missing { opacity: 0.55; }
.badge {
  display: inline-block;
  min-width: 44px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #e6f0ff;
  color: #1746a2;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}
table { width: 100%; border-collapse: collapse; }
td, th { padding: 8px 6px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.bar { height: 12px; min-width: 80px; background: #e5e7eb; border-radius: 6px; overflow: hidden; }
.fill { height: 100%; background: var(--green); }
.warn { border-color: #f59e0b; background: #fffbeb; }
footer { padding: 22px 32px 34px; color: var(--muted); font-size: 13px; }
@media (max-width: 760px) {
  header, .stats, .links { padding-left: 16px; padding-right: 16px; }
  h2 { margin-left: 16px; margin-right: 16px; }
  .panel { margin-left: 16px; margin-right: 16px; }
  .builder { grid-template-columns: 1fr; }
  .command { grid-template-columns: 1fr; }
  .pair-grid { grid-template-columns: 1fr; }
}
</style>"""
