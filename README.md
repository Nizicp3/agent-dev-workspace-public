# 归藏PPT设计智能体 · 项目总览

> 基于 guizang-ppt-skill 重构，适配浦发银行智能体创设平台 + Markdown转换器插件
> 项目状态：**技术验证完成，待端到端部署测试**
> 最后更新：2026-09-12

---

## 项目目标

将开源项目 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)（24K+ stars）的排版与风格能力，重构为可在**浦发银行智能体创设平台**（agent.spdb.com）上运行的独立智能体。通过平台已验证的「Markdown转换器」MCP插件导出 HTML 格式的演示文稿和数据看板。

## 核心决策

| 决策 | 结论 | 原因 |
|---|---|---|
| 主输出格式 | **HTML only**（非PPTX） | md_to_pptx 几乎无样式效果，已废弃 |
| 图片生成 | **不做** | 平台图片生成能力不可靠，排版风格为核心 |
| 样式注入方式 | **`<style>` 块 + class选择器** | 已验证可透传 |
| CSS位置 | **系统提示词**，非对话粘贴 | 对话粘贴会被大模型复述截断 |
| 单次输出长度 | **< 1000字符**（多行格式） | 超过则大模型构造插件调用时截断 |
| 版式数量 | **8种已实现**（L1-L8） | 32种为guizang原始设计目标 |
| 主题色 | **IKB蓝1套**（#002FA7） | 9套为未来扩展 |
| 工作流 | **单Agent线性6步** | 5工作流为未来拆分目标 |

## 文档基线层级（权威顺序）

```
docs/04-技术验证记录.md  ← 事实层（9轮实测，不可变）
system-prompt/system-prompt.md  ← 执行层（部署用，权威）
docs/01-方案设计-v2.1.md  ← 设计层（与执行层对齐，v3.0基线对齐版）
css-templates/ layouts/  ← 资产层（与执行层一致）
test-cases/  ← 验证层
```

凡文档间冲突，以上层为准。已完成全仓库基线对齐，消除7处内部矛盾。

## 已验证的技术约束（红线）

经过 9 轮实测，确认以下规则：

### 可行
- `<style>` 标签完整保留
- class 选择器正常
- 大写十六进制颜色（#002FA7）
- font-family: sans-serif（单一字体名）
- 原始 HTML div 保留
- flexbox 布局
- 内联 style 属性
- CSS 条形图（height 百分比）
- 多行格式，每行一条 CSS 规则
- 总长度 ~1000 字符可完整输出

### 禁忌
| 禁忌 | 现象 |
|---|---|
| 单引号 | 输入直接截断 |
| 逗号分隔多字体名 | 在 font-family 处截断 |
| 元素选择器 h1/h2/h3 | 被插空格变成 h 1 |
| 小写十六进制 | 被插空格 |
| md_text > ~1200字符 | 大模型输出截断 |
| @keyframes / 动画 | 输出空白 |
| CSS Grid / clamp() | 可能导致空白 |
| 单行压缩CSS | 即使<1000字符也会截断 |
| 对话中粘贴长文本让大模型转述 | 大模型复述时提前停止 |

## 项目结构

```
├── README.md                          # 本文件
├── docs/
│   ├── 01-方案设计-v2.1.md            # 方案设计（v3.0基线对齐版）
│   ├── 02-完整配置方案-v1.0.md        # 系统提示词+版式库+测试用例
│   ├── 03-架构图.html                 # 智能体架构图
│   └── 04-技术验证记录.md             # 全部9轮测试结果+根因分析
├── system-prompt/
│   └── system-prompt.md               # 可直接复制到平台的系统提示词（权威执行口径）
├── css-templates/
│   ├── core.css                       # 核心CSS（封面+内容+表格，与system-prompt一致）
│   └── dashboard.css                  # 仪表盘CSS（KPI+条形图+双栏+进度条）
├── layouts/
│   └── layout-library.md              # 8种核心版式的HTML示例（已实现）
├── test-cases/
│   ├── 01-baseline-test.md            # 基线测试（已验证成功）
│   ├── 02-mini-dashboard.md           # 迷你仪表盘（已验证成功）
│   ├── 03-interactive-dashboard.md    # 交互仪表盘（hover效果，待验证）
│   └── 04-dash-1000-test.md           # 1000字符边界测试
├── hiagent-workflow-builder/          # HiAgent工作流生成Skill（已安装验证）
├── hiagent-project/                    # HiAgent项目完整材料（另一个项目）
└── related-projects/                  # 相关参赛项目材料
```

## 当前状态与下一步

### 已完成
- guizang-ppt-skill 源码完整调研
- 方案设计 v3.0（基线对齐：HTML only、8版式、1主题色、单Agent线性流程）
- 全仓库文档基线统一（消除7处内部矛盾）
- 架构图设计
- Markdown转换器插件参数确认
- CSS注入验证（style + class选择器 + 大写hex 可透传）
- 技术约束边界探明（9轮测试，禁忌清单已确认）
- 迷你仪表盘验证成功（KPI+条形图+双栏+进度条）
- 系统提示词（可直接部署）
- hiagent-workflow-builder Skill 安装与本地验证

### 待完成
- 系统提示词部署到平台后的端到端测试
- 交互效果验证（:hover）
- 系统提示词模式下的长度上限探索（1200/1500/2000）
- 多文件拆分导出验证
- 主题切换验证
- 暗色背景页面验证

### 下一步
1. 部署智能体：将 system-prompt/system-prompt.md 复制到平台系统提示词，绑定 Markdown转换器插件
2. 端到端测试：用自然语言指令测试（如做一个工作日报数据看板）
3. 交互验证：确认 :hover 等CSS交互在生成的HTML中生效
4. 长度边界探测：系统提示词模式下测试更长内容是否可行
5. 多页演示：验证多文件拆分导出流程

## 关键技术洞察

### 为什么对话粘贴长文本会失败？
用户在对话框粘贴 Markdown 并说转换成html时，平台大模型需要复述整段文本到 md_text 参数。大模型作为传声筒不稳定，经常在复述过程中提前停止。解决方案：CSS模板放系统提示词，用户只用自然语言描述需求，智能体自主生成内容。

### 为什么多行格式必须每行一条CSS？
单行压缩的CSS即使总长度<1000字符也会被截断。推测平台文本处理层对超长单行有处理问题。解决方案：始终使用多行格式。

### 为什么PPTX放弃了？
md_to_pptx 输出的文件几乎不保留任何CSS样式——表格无颜色、标题无字号、引用无边框。投入产出比极低。HTML路径通过CSS注入可实现高保真排版。

## 如何用 WorkBuddy / Codex 继续开发

1. Clone 本仓库到本地
2. 阅读 README.md 了解全局
3. 阅读 docs/04-技术验证记录.md 了解所有踩坑和硬约束（事实层）
4. 阅读 system-prompt/system-prompt.md 了解当前执行口径（执行层）
5. 阅读 docs/01-方案设计-v2.1.md 了解设计意图和未来目标（设计层）
6. 根据当前状态与下一步继续推进
7. 所有CSS修改必须遵守 docs/04 中的禁忌清单，所有class名必须与 system-prompt 一致

## 相关链接

- guizang-ppt-skill: https://github.com/op7418/guizang-ppt-skill
- 浦发银行智能体创设平台: agent.spdb.com
- IKB克莱因蓝: #002FA7
