# HiAgent兼容性与安全边界

## 已验证范围

- 顶层 AppConfig / AppDepends / AppInfo 原生包装。
- AppConfig.ChatFlowDetail.DLVersion: v2。
- Start、Code、LLM、End 节点。
- LLM文本输出 raw_output。
- End的 OutputType: Variable 和显式变量映射。
- Start字符串输入 Type: 0。
- Start附件列表输入 Type: 11，子字段 name、url。

## 默认禁止

- Condition或其他分支节点。
- 工作流调用工作流。
- 插件、外部API、数据库或工具节点。
- 工作流内部知识库检索节点。
- 智能体跨环境导入包。
- 未验证模型参数、思维模式或多智能体结构。

## 知识库边界

目标环境可能把多个来源文件放在同一个知识库。推荐做法：
1. 在智能体界面手工挂载实际知识库。
2. 把检索结果作为 Start 字符串输入。
3. LLM提示词要求输出实际来源文件名。
4. 不在 YAML 中虚构多个知识库ID。

## 本地校验不证明的事项

- 目标公司平台版本完全一致。
- 模型ID和工作空间ID当前仍有效。
- HiAgent真实模型运行一定返回内容。
- 附件已经被平台解析。

## 扩展能力的准入条件

1. 从目标公司 HiAgent 创建最小工作流并原生导出 YAML。
2. 保存脱敏后的原生样本和平台版本信息。
3. 明确该节点输入、输出、依赖及顶层 Depends 映射。
4. 加入生成器行为测试。
5. 在目标公司测试环境重新导入生成文件。
6. 运行最小用例。
