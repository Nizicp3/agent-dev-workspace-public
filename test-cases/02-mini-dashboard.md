# 测试用例 02：迷你仪表盘

**状态**：✅ 已验证成功（关键里程碑）
**日期**：2026-09-12

## 测试目标
验证 ~1000 字符、多行格式下，完整仪表盘布局（KPI+条形图+双栏+进度条）是否正常渲染。

## 输入
output_filename: dash-mini.html

md_text（约1000字符，多行格式）:
```markdown
<style>
.b{background:#F0EDE6;font-family:sans-serif;padding:32px;color:#0A0A0B}
.t{font-size:32px;font-weight:200;margin-bottom:20px}
.t em{color:#002FA7;font-style:italic}
.r{display:flex;gap:12px;margin-bottom:24px}
.c{flex:1;background:#FFF;border-top:3px solid #002FA7;padding:16px}
.l{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#999;margin-bottom:12px}
.v{font-size:36px;font-weight:200}
.ch{background:#FFF;padding:16px;margin-bottom:24px}
.bs{display:flex;align-items:flex-end;gap:8px;height:120px}
.bc{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.bf{width:60%;background:#002FA7}
.bl{font-size:11px;margin-top:8px;color:#777}
.g{display:flex;gap:16px}
.co{flex:1;background:#FFF;padding:14px}
.it{display:flex;padding:6px 0;border-bottom:1px solid #EEE;font-size:12px}
.st{width:6px;height:6px;margin-right:8px;margin-top:5px;background:#1A7F37}
.pt{height:6px;background:#EEE;margin:4px 0}
.pf{height:100%;background:#002FA7}
.ct{font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:#002FA7;margin-bottom:8px}
</style>
<div class="b">
<div class="t">工作日报 <em>· 数据看板</em></div>
<div class="r">
<div class="c"><div class="l">今日完成</div><div class="v">23</div></div>
<div class="c"><div class="l">进行中</div><div class="v">7</div></div>
<div class="c"><div class="l">代码提交</div><div class="v">147</div></div>
</div>
<div class="ct">本周产出趋势</div>
<div class="ch">
<div class="bs">
<div class="bc"><div class="bf" style="height:45%"></div><div class="bl">周一</div></div>
<div class="bc"><div class="bf" style="height:56%"></div><div class="bl">周二</div></div>
<div class="bc"><div class="bf" style="height:74%"></div><div class="bl">周五</div></div>
<div class="bc"><div class="bf" style="height:28%"></div><div class="bl">周六</div></div>
</div>
</div>
<div class="g">
<div class="co">
<div class="ct">任务清单</div>
<div class="it"><div class="st"></div>登录模块重构</div>
<div class="it"><div class="st"></div>API压测报告</div>
<div class="it"><div class="st" style="background:#D4A017"></div>看板联调中</div>
</div>
<div class="co">
<div class="ct">项目进度</div>
<div class="it">数据中台 <span style="margin-left:auto">87%</span></div>
<div class="pt"><div class="pf" style="width:87%"></div></div>
<div class="it">移动端 <span style="margin-left:auto">62%</span></div>
<div class="pt"><div class="pf" style="width:62%"></div></div>
</div>
</div>
</div>
```

## 结果
- ✅ 源码55行完整保留，无截断
- ✅ KPI卡片（3张，顶部蓝色色条）
- ✅ CSS条形图（4根柱子，高度按百分比）
- ✅ 双栏布局（左任务清单+右进度条）
- ✅ 进度条（蓝色填充）
- ✅ 状态点（绿/黄）
- ✅ flexbox布局全部正常

## 关键确认
- ~1000字符是安全边界
- 多行格式（每行一条CSS）必须
- 仪表盘级别的复杂排版完全可行
