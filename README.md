# eval-sample-curator

`eval-sample-curator` 是一个离线 CLI，用来从 LLM eval、prompt regression、RAG eval 的 JSONL/CSV 结果里，自动挑出最值得人工复盘的一小批样本。它面向真实评审流程：优先暴露失败簇、边界分数、成本/延迟异常、模型间分歧、回归样本，并在导出 review packet 前做近重复压制和 PII redaction。

它不是在线服务，也不需要 GitHub token、模型 API key 或外部数据库。

## 适用场景

- 每次 prompt 或模型版本变更后，从上千条 eval 结果里挑 20 条最该人工看的样本。
- RAG eval 中优先复盘检索/生成失败、边界得分和慢请求。
- 多模型 A/B 对比时找出同一 case 上通过/失败不一致的样本。
- 把 review packet 交给产品、QA、领域专家，用 Markdown/JSON/CSV 协作复盘。

## 安装

```bash
python -m pip install -e ".[dev]"
```

Python 版本要求：3.9+。运行时默认不依赖第三方库，测试仅使用 `pytest`。

## 快速开始

```bash
curate examples/results.jsonl \
  --format markdown \
  --rules examples/rules.json \
  --limit 20 \
  --output packet.md
```

检查是否能选出样本，不写入文件：

```bash
curate examples/results.jsonl --rules examples/rules.json --check
```

`--check` 在至少选出 1 条样本时退出码为 `0`，否则为 `1`。这适合放在 CI 或 nightly eval 流程里。

## 输入格式

支持 `.jsonl` 和 `.csv`。默认字段：

| 语义 | 默认字段 |
| --- | --- |
| 样本 ID | `id` |
| Prompt | `prompt` |
| 模型输出 | `output` |
| 期望结果 | `expected` |
| 分数 | `score` |
| 是否通过 | `passed` |
| 模型名 | `model` |
| 延迟 | `latency_ms` |
| 成本 | `cost_usd` |
| 标签 | `tags` |

字段可以在规则文件中配置：

```json
{
  "fields": {
    "id": "case_id",
    "prompt": "input",
    "output": "actual",
    "expected": "golden",
    "score": "judge_score",
    "passed": "ok",
    "model": "model_name",
    "latency_ms": "latency",
    "cost_usd": "cost",
    "tags": "labels"
  }
}
```

`tags` 支持 JSON 数组、逗号分隔或分号分隔。

## 选择策略

当前策略按可解释优先级选择样本，每条入选样本都会导出 `reasons` 和 `evidence`：

- `failure`：`passed=false` 的失败样本优先。
- `regression`：包含 `regression` / `regressed` tag，或 raw 字段里有真值型 `regression` 标记。
- `score_band`：分数落在边界区间，例如 `[0.45, 0.75]`。
- `latency_outlier`：延迟高于均值加 z-score 阈值。
- `cost_outlier`：成本高于均值加 z-score 阈值。
- `model_disagreement`：同一 `id` 下不同模型的 `passed` 结果不一致。
- `tag_quotas`：把指定标签的样本提前，避免 review packet 被单一类型占满。
- `near_duplicate_threshold`：用标准库实现的 token Jaccard 相似度压制近重复样本。
- `redact_pii`：导出前脱敏 email、手机号、SSN、信用卡样式数字、IPv4。

## 规则文件

```json
{
  "score_band": [0.45, 0.75],
  "tag_quotas": {
    "rag": 5,
    "regression": 5
  },
  "near_duplicate_threshold": 0.82,
  "latency_outlier_z": 1.5,
  "cost_outlier_z": 1.5,
  "redact_pii": true
}
```

## 导出格式

Markdown 适合人工复盘：

```bash
curate examples/results.jsonl --format markdown --output packet.md
```

JSON 适合下游系统：

```bash
curate examples/results.jsonl --format json --output packet.json
```

CSV 适合表格协作：

```bash
curate examples/results.csv --format csv --output packet.csv
```

## 测试

```bash
python -m pytest
```

测试覆盖 loader、selection strategy、dedupe、redaction、report 和 CLI exit codes。

## 限制

- 近重复检测使用简单 token/Jaccard，不做语义 embedding。
- 离群值检测使用全局均值和总体标准差，适合轻量离线筛选，不替代严谨统计分析。
- 模型分歧默认按同一 `id` 分组；如果你的数据把不同模型结果写成不同 ID，需要先在上游标准化。
- PII redaction 是规则型保护层，不保证覆盖所有个人信息形态。

## English

`eval-sample-curator` is an offline command-line tool for selecting a compact, high-value human review packet from LLM evaluation results. It is designed for developers and product teams working on LLM evals, prompt regression testing, and RAG evaluation.

The tool reads JSONL or CSV files, applies configurable field mappings, scores samples with explainable reasons, suppresses near-duplicates, optionally redacts common PII patterns, and exports the selected review packet as Markdown, JSON, or CSV.

### Install

```bash
python -m pip install -e ".[dev]"
```

Python 3.9+ is required. Runtime code uses the Python standard library only. Tests use `pytest`.

### CLI

```bash
curate INPUT \
  --format markdown|json|csv \
  --rules rules.json \
  --limit 20 \
  --output packet.md \
  --check
```

`--check` writes no report. It exits `0` if at least one sample would be selected and `1` otherwise.

### Supported Signals

- Failures first.
- Boundary score bands.
- Latency and cost outliers.
- Model disagreement on the same sample ID.
- Regression-tagged samples.
- Tag quotas for review packet diversity.
- Near-duplicate suppression with token Jaccard similarity.
- Rule-based PII redaction for exported packets.

### Configuration

Rules are provided as JSON. You can configure field names, score band, tag quotas, dedupe threshold, outlier thresholds, and PII redaction.

### Known Limitations

Near-duplicate suppression is lexical, not semantic. Outlier detection is a lightweight global heuristic. Model disagreement is grouped by `id`. PII redaction is regex-based and should be treated as a review aid, not a compliance guarantee.
