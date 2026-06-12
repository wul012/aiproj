# Versioned Artifacts

Versioned artifacts make the project auditable. For v1098 and later model-governance and maintenance work, runtime evidence is stored under `f/`.

Typical layout:

```text
f/<version>/图片
f/<version>/解释/说明.md
f/<version>/解释/<report-name>/*.json
f/<version>/解释/<report-name>/*.csv
f/<version>/解释/<report-name>/*.txt
f/<version>/解释/<report-name>/*.md
f/<version>/解释/<report-name>/*.html
```

The screenshot proves the HTML report can be opened and read. The JSON is the machine-readable source of truth. CSV helps comparison. Markdown and text make command-line review easier.

Versioned artifacts should be referenced from README and stage-specific code explanations so a reader can move from concept to evidence without guessing file names.

For late-stage maintenance review, [Artifact map](artifact-map.md) summarizes recent `f/<version>` folders and counts screenshots plus JSON/CSV/Markdown/HTML reports.
