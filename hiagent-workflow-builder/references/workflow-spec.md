# 工作流规格契约

## 顶层字段

```json
{
  "spec_version": "1.0",
  "workflow_key": "稳定唯一标识-v1",
  "name": "HiAgent中显示的工作流名称",
  "description": "工作流用途",
  "inputs": [],
  "steps": [],
  "outputs": {}
}
```

## Start 输入

字符串：{"name": "query", "description": "用户问题", "required": true, "type": "string"}
附件列表：{"name": "files", "description": "用户上传的附件", "required": false, "type": "file_list"}

## Code 步骤

```json
{
  "id": "normalize",
  "type": "code",
  "name": "输入归一",
  "code": "def handler(params):\n    return {\"safe_query\": str(params.get(\"query\", \"\")).strip()}",
  "inputs": {"query": "start.query"},
  "outputs": ["safe_query"]
}
```

约束：入口函数必须为 handler(params)；inputs 右侧是 上游步骤ID.输出字段；Start 固定使用逻辑 ID start。

## LLM 步骤

```json
{
  "id": "answer",
  "type": "llm",
  "name": "生成答复",
  "system_prompt": "只能依据输入证据回答。",
  "prompt": "用户问题：{{query}}\n证据：{{evidence}}",
  "inputs": {"query": "normalize.safe_query", "evidence": "start.knowledge_context"},
  "max_tokens": 1024,
  "temperature": 0.1,
  "top_p": 0.9
}
```

约束：prompt 中每个 {{变量}} 必须在 inputs 中出现；LLM文本输出字段固定为 raw_output。

## End 输出

{"outputs": {"reply": "answer.raw_output"}}

至少配置一个输出；LLM输出必须引用 .raw_output。

## 连线规则

步骤按照 steps 顺序生成。一个步骤只能引用 Start 或排在它前面的步骤。
