# Publication Receipts

Publication receipt reports record how a governance artifact may be consumed downstream. The common loop is:

```text
record receipt -> contract check -> index -> review -> next receipt
```

A receipt can be `lookup-only`, which means it is useful for downstream governance lookup, audit, and traceability. It does not mean the model is approved for production promotion.

The receipt chain normally includes:

- a script entry point
- a source module
- an artifact renderer
- a focused test file
- JSON/CSV/text/Markdown/HTML outputs
- a screenshot and explanation under `f/<version>`
- a code explanation when the version changes code or governance behavior

From v1130 onward, new publication receipt tooling should prefer shorter aliases such as `pub_receipt_index`, `pub_receipt_review`, and `receipt_contract_check`.
