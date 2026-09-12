# 影刀浏览器会话与 Python HTTP 报表下载

## 1. 适用边界

当用户已能在浏览器手工查询或下载报表，但需要自动处理多日期、多页或大量记录时，优先复现网页 HTTP 请求。低码只保留必要的网页登录或入口点击。

下列情况保留浏览器自动化：请求依赖客户端证书或不可导出的浏览器状态；接口使用方式尚未获得授权；没有可稳定识别的查询或下载请求；服务端明确禁止非页面调用。

## 2. 事实来源顺序

1. 当前办公环境中一次手工成功请求
2. 该请求的 Request URL、Headers、Query/Payload 和 Response
3. 影刀实际生成的 Python 或流程代码
4. 当前客户端截图和节点帮助
5. 历史 SOP、旧脚本和通用经验

低码节点可用不证明 Python 包存在同名 API。

## 3. 会话和请求契约

从同一次成功查询请求中获取完整会话材料：Cookie 请求头、完整 Referer、Referer 中的 token/CSRF 等短期参数、查询 URL 和全部业务参数、下载 URL 和响应文件名。

若目标会话将 Cookie 与 Referer/token 绑定，应从同一有效会话取得并按绑定关系更新。

发请求前比较 Referer 和查询中的上下文字段，仅对目标契约要求一致的字段作相等校验。

## 4. 实现步骤

### A. 最小查询探针
第一版只查询第一页，返回 HTTP 状态、业务 code 和 msg、total 和 row_count、实际查询参数摘要、脱敏会话摘要。

### B. 全部分页
从第一页读取 total，按网页已验证的 pageSize 循环，每页收集非空 reportId，去重，空页时停止。

### C. 批量下载
将全部 reportId 按接口约定拼接，使用同一 Cookie 和 Referer，读取 Content-Disposition 文件名，在内存中确认响应是有效 ZIP，验证通过后再写入下载目录。

## 5. 安全与脱敏诊断

允许输出：Cookie 名称和每项值长度、Cookie 项目数量、Referer 的协议和脱敏主机/路径、token 是否存在及长度、查询参数的脱敏摘要、响应 code/total/row_count。

禁止输出：Cookie 原值、token 原值、密码或完整认证头、未脱敏的请求转储。

## 6. 已验证故障模式

| 现象 | 根因或结论 |
| --- | --- |
| module xbot has no attribute browser | 低码浏览器能力不等于 Python API |
| 360 插件已安装仍无法附着 | 浏览器产品、插件和高码运行时边界不一致 |
| invalid handle | 新窗口/CEF/浏览器对象句柄不稳定 |
| 网页监听结果为空 | 监听期间未触发请求，或监听了错误网页对象 |
| 只有三项 Cookie | 不能据此判断会话缺失 |
| Cookie 正确但 total=0 | 检查完整 Referer 和业务上下文 |
| HTTP 200 但 total=0 | 仍可能是 appId 等上下文参数错误 |
| 下载生成 ZIP 但无法打开 | 服务端返回了 JSON/HTML 错误页 |

核心教训：同一次成功请求是唯一事实来源。