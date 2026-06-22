# examples —— 可跑示例

这里放可直接运行的小示例，配合 `lessons/` 的讲义理解原理。

## extractor.py —— LLM 记忆提取器

参考 mem0 的 `FACT_RETRIEVAL_PROMPT` 思路（用自己的话重写，未照抄），演示如何用 LLM 从对话里提取结构化记忆（内容 / 分类 / 重要性 / 实体 / 置信度），并做容错 JSON 解析 + 重试。

### 运行

```bash
pip install openai
export GLM_API_KEY=你的key           # 或 ZHIPU_API_KEY / KIMI_API_KEY
python extractor.py                  # 用内置的 3 条合成对话自测
```

默认调用 GLM-4-Flash（端点 `open.bigmodel.cn`，可用 `GLM_BASE_URL` / `GLM_MODEL` 覆盖）。

### 输入数据

`sample_dialogs.jsonl` 是一份**合成**的小样例（每行一个对话），仅用于跑通流程，不含任何真实个人数据。

> 说明：作者原始评测用的真实对话数据集、人工标注 ground truth 与 F1 对比报告，因含个人/内部信息**未包含在本仓库**。如需做定量评测，请用你自己的数据按 `sample_dialogs.jsonl` 的格式准备，并自行标注 ground truth。
