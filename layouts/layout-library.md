# 版式库 · 8种核心版式

> 每种版式包含完整HTML示例，可直接使用
> 所有版式需配合 css-templates/ 中的CSS模板使用

---

## L1 封面页

**用途**：演示文稿第一页，标题+副标题+日期

```html
<div class="p">
<div class="hd">
<div class="ti">主标题 <em>· 副标题</em></div>
<div class="dt">2026.09.12<span style="display:block;color:#999;font-weight:400">WEEK 37</span></div>
</div>
<div style="margin-top:40px;font-size:15px;color:#666;max-width:60vw">一句话描述或引言</div>
<div class="ft"><span>GUIZANG</span><span>2026</span></div>
</div>
```

## L2 KPI概览

**用途**：3-4个关键指标卡片展示

```html
<div class="p">
<div class="sec">核心指标 · KEY METRICS</div>
<div class="r">
<div class="c"><div class="cl">今日完成</div><div class="cv">23</div></div>
<div class="c"><div class="cl">代码提交</div><div class="cv">147</div></div>
<div class="c"><div class="cl">缺陷率</div><div class="cv">2.1%</div></div>
</div>
</div>
```

## L3 条形图

**用途**：CSS实现的垂直条形图，高度用内联style百分比

```html
<div class="p">
<div class="sec">产出趋势 · WEEKLY TREND</div>
<div class="bs">
<div class="bc"><div class="bf lt" style="height:45%"></div><div class="bl">周一</div></div>
<div class="bc"><div class="bf lt" style="height:56%"></div><div class="bl">周二</div></div>
<div class="bc"><div class="bf" style="height:67%"></div><div class="bl">周四</div></div>
<div class="bc"><div class="bf dk" style="height:74%"></div><div class="bl">周五</div></div>
<div class="bc"><div class="bf lt" style="height:28%"></div><div class="bl">周六</div></div>
</div>
</div>
```

## L4 双栏看板

```html
<div class="p">
<div class="g">
<div class="co">
<div class="ct">任务清单 <span style="font-size:9px;font-weight:700;background:#002FA7;color:#FFF;padding:2px 7px;letter-spacing:1px">6</span></div>
<div class="it"><div class="dot done"></div>登录模块重构<span class="ow">张伟</span></div>
<div class="it"><div class="dot done"></div>API网关压测<span class="ow">李娜</span></div>
<div class="it"><div class="dot doing"></div>看板前端联调<span class="ow">王磊</span></div>
<div class="it"><div class="dot todo"></div>周会材料准备<span class="ow">刘洋</span></div>
</div>
<div class="co">
<div class="ct">项目进度</div>
<div class="pr"><div class="pl"><span>数据中台V2</span><span class="pp">87%</span></div><div class="pt"><div class="pf" style="width:87%"></div></div></div>
<div class="pr"><div class="pl"><span>移动端改版</span><span class="pp">62%</span></div><div class="pt"><div class="pf" style="width:62%"></div></div></div>
<div class="pr"><div class="pl"><span>支付系统升级</span><span class="pp">45%</span></div><div class="pt"><div class="pf warn" style="width:45%"></div></div></div>
<div class="pr"><div class="pl"><span>客户画像系统</span><span class="pp">23%</span></div><div class="pt"><div class="pf danger" style="width:23%"></div></div></div>
</div>
</div>
</div>
```

## L5 数据表格

```html
<div class="p">
<div class="sec">指标明细</div>
<table>
<tr><th>指标</th><th>今日</th><th>环比</th></tr>
<tr><td>DAU</td><td>12,847</td><td style="color:#1A7F37">+5.2%</td></tr>
<tr><td>新增用户</td><td>326</td><td style="color:#1A7F37">+12.4%</td></tr>
<tr><td>留存率</td><td>68.3%</td><td style="color:#CF222E">-1.1%</td></tr>
</table>
</div>
```

## L6 引言金句

```html
<div class="p">
<div class="q">这东西在三年前，需要一个十人团队做一年。</div>
<div style="font-size:12px;color:#999;margin-top:8px">—— 一个观察者的判断</div>
</div>
```

## L7 三栏内容

```html
<div class="p">
<div class="sec">三大策略</div>
<div class="r">
<div class="c"><div class="ct">策略一</div><div style="font-size:13px;line-height:1.6;color:#555">详细描述内容</div></div>
<div class="c"><div class="ct">策略二</div><div style="font-size:13px;line-height:1.6;color:#555">详细描述内容</div></div>
<div class="c"><div class="ct">策略三</div><div style="font-size:13px;line-height:1.6;color:#555">详细描述内容</div></div>
</div>
</div>
```

## L8 结束页

```html
<div class="p" style="display:flex;flex-direction:column;justify-content:center;min-height:70vh">
<div class="ti" style="text-align:center">谢谢 <em>· Thank You</em></div>
<div style="text-align:center;font-size:14px;color:#666;margin-top:20px">联系人 · 邮箱 · 日期</div>
</div>
```

## 版式组合建议

| 场景 | 推荐版式组合 |
|---|---|
| 工作日报 | L1 → L2 → L3 → L4 → L8 |
| 项目复盘 | L1 → L2 → L5 → L6 → L8 |
| 季度汇报 | L1 → L7 → L2 → L5 → L6 → L8 |
| 产品发布 | L1 → L6 → L7 → L2 → L8 |
| 数据看板（单页） | L2 + L3 + L4 合并在一个 .p 中 |
