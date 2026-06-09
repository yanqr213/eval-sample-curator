# Changelog

## 0.2.0 - 2026-06-09

- Added `pr-comment` output for compact PR/CI review summaries.
- Made `--check` skip report writing, matching the documented CI gate behavior.
- Added CI smoke coverage for Markdown and PR comment packet generation.

## 0.1.0 - 2026-06-08

- Initial local release.
- Added offline JSONL/CSV loading with configurable field mapping.
- Added sample curation for failures, boundary scores, latency/cost outliers, model disagreement, regression tags, tag quotas, near-duplicate suppression, and PII redaction.
- Added Markdown, JSON, and CSV review packet exporters.
- Added CLI, examples, tests, and GitHub Actions CI configuration.
