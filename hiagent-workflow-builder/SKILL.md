---
name: hiagent-workflow-builder
description: 为公司 HiAgent 平台设计并生成可直接导入的原生工作流 YAML；适用于新建 Start/Code/LLM/End 工作流、检查变量引用和生成导入前校验报告。不要用于生成可跨环境导入的智能体包，也不要猜测未验证节点。
allowed-tools: Read, Write, Bash
---

# HiAgent 工作流生成器

把业务需求转换为受约束的 JSON 规格，再调用本 Skill 的确定性脚本生成 HiAgent YAML。不要直接手写最终 YAML。

## 适用边界

- 只生成 `Start`、`Code`、`LLM`、`End` 节点。
- 只使用 `string` 和 `file_list` 两种 Start 输入。
- LLM 文本输出固定引用 `raw_output`；End 必须显式映射至少一个输出。
- 不生成 Condition、知识库节点、插件节点、子工作流调用、智能体导入包或其他未验证结构。
- 知识库检索由目标 HiAgent 智能体侧手工挂载；工作流只接收已检索到的文本输入。
- 本地校验通过不等于公司端验真完成。最终必须在目标 HiAgent 导入并运行至少一条用例。

## 执行流程

1. 明确工作流名称、用途、Start 输入、处理步骤和 End 输出。信息不足时逐项询问。
2. 读取 references/workflow-spec.md，按照契约创建 UTF-8 JSON 规格文件。
3. 要求用户提供目标环境的 workspace_id、model.id 和 model.name。
4. 不接受密码、Token、API Key、客户资料或真实业务附件。
5. 运行生成器：python scripts/hiagent_workflow.py generate --spec <规格JSON> --profile <环境JSON> --output-dir <输出目录>
6. 确认命令退出码为 0，读取 *.validation.json，只有 status 为 pass 才可交付 YAML。
7. 向用户同时交付：YAML文件、validation.json、公司端导入与运行验收说明。

## 失败处理

- 不支持的节点类型：停止生成，说明不在已验证能力内。
- 不存在的输入/输出引用：修正规格，不得删除校验。
- 提示词变量未绑定：补齐映射或从 prompt 删除。
- 仍是占位符：要求用户确认真实环境 ID。
- Python 无法运行：交付 JSON 规格并说明生成被阻断，不退化为手写 YAML。

## 输出表述

区分三种状态：本地静态校验通过、公司端导入通过、公司端运行通过。没有后两类证据时，不得声称已经可以直接上线。
