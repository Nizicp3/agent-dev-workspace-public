# 测试用例 01：CSS注入基线测试

**状态**：✅ 已验证成功
**日期**：2026-09-12

## 测试目标
验证 md_to_html 是否保留 Markdown 中的 `<style>` 标签和 CSS 内容。

## 输入
output_filename: css-injection-test.html

md_text:
```markdown
<style>
  body { background: #f1efea; font-family: sans-serif; padding: 48px; }
  .guizang-marker { color: #002FA7; font-size: 48px; font-weight: 200; }
  .guizang-check { border-left: 4px solid #002FA7; padding: 8px 16px; font-size: 20px; }
</style>

<div class="guizang-marker">CSS 注入测试</div>

<div class="guizang-check">如果这行字左边有 4px 蓝色竖线 → CSS 生效</div>
```

## 结果
- ✅ `<style>` 标签完整保留
- ✅ CSS 内容原样保留（#002FA7、font-size:48px 等）
- ✅ `<div class="...">` 元素保留
- ✅ 视觉效果生效（蓝色大标题、蓝色左边框）

## 确认的能力
- `<style>` 标签可透传
- class 选择器正常
- 大写十六进制正常
- 原始 HTML div 保留
