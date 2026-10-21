---
name: reimbursement-material-organizer
description: Use when Codex needs to set up a reusable reimbursement profile or collect, verify, classify, deduplicate, summarize, and audit travel reimbursement invoices and attachments from available mailboxes or local files, including multi-currency expenses, itinerary reconstruction, and missing-ticket checks.
---

# 报销材料整理

## 概述

把邮箱与本地文件中的差旅凭证整理为可复核的分类材料、金额汇总、每日行程和缺票检查。把通用规则与公司预设分开，并把非敏感用户档案保存在 Skill 安装目录之外。

## 快速判断

| 当前需求 | 操作 |
| --- | --- |
| 首次使用、查看或更新档案 | 读取 [档案字段](references/profile-fields.md)，运行 `scripts/profile_manager.py` |
| 整理通用报销材料 | 读取 [通用规则](references/core-rules.md) 与 [输出规范](references/output-spec.md) |
| 档案启用 `hutong` 预设 | 额外读取 [智慧互通预设](references/presets/hutong.md) |
| 有适配的邮箱能力 | 只读搜索并下载候选附件，再与本地材料合并 |
| 没有邮箱能力或登录失败 | 继续本地材料模式，并报告尚需用户补充的材料 |

规则优先级始终为：本次任务 > 用户档案 > 公司预设 > 通用规则。

## 管理用户档案

从本 Skill 所在目录运行：

```bash
python3 scripts/profile_manager.py path
python3 scripts/profile_manager.py show
python3 scripts/profile_manager.py validate <临时档案.json>
python3 scripts/profile_manager.py save <临时档案.json>
```

档案不存在时，按 [档案字段](references/profile-fields.md) 收集基础信息，先校验再保存。提醒用户不要提供邮箱密码、访问令牌、Cookie、API Key 或其他凭据。`show` 默认隐藏税号。更新现有档案前展示变更摘要，取得确认后使用 `save --force`。

不要把档案、临时 JSON、凭据或真实报销材料放入 Skill 目录。

## 执行一次整理

1. 读取并校验用户档案。
2. 确认差旅开始日期、结束日期、城市或关键词，以及可选的本地材料位置。缺少会实质改变结果的信息时再询问。
3. 读取通用规则、输出规范和已启用的公司预设；按规则优先级合并冲突项。
4. 检测当前可用的邮箱能力。只使用与用户邮箱匹配且已连接的只读搜索、读取和附件下载能力；不因为缺少邮箱工具而停止。
5. 搜索开始日前 1 天至结束日后 30 天的相关邮件；用户或预设明确了其他窗口时使用高优先级设置。结合日期、出行人、城市、发件人、主题、正文和附件名筛选。
6. 合并邮箱附件与本地材料。打开 PDF、XML、OFD、图片等实际内容，核对日期、人员、城市、起终点、金额和币种；不能只按邮件主题或文件名归类。
7. 识别同一发票或订单的多种格式和辅助材料。保留有效原件，但每个计算项只计一次。
8. 按规则分类并分币种汇总。金额、币种、归属或重复关系无法确认时，保留材料并标为“待复核”，不得猜测。
9. 依据跨城票据、住宿和本地交通重建每日行程，逐段检查跨城或跨地区票据。
10. 按输出规范写入分类清单、`整理摘要.txt` 和 `检查.txt`。
11. 报告搜索范围、数据来源、候选与纳入数量、分类金额、币种小计、待复核项和疑似缺失票据。

## 安全边界

- 邮箱操作只限搜索、读取和下载附件；不得发送、转发、归档、删除、移动邮件或修改标签。
- 不得删除、移动或覆盖原始本地材料。需要归档时复制到输出目录。
- 输出目录已有内容时先扫描并合并；重名文件使用日期、平台或短哈希区分，不得静默覆盖。
- 不得把不同币种强行相加或自行采用汇率。只有材料明确给出人民币实付或用户提供汇率时才能折算，并保留原币说明。
- 不得把行程单、入住证明、水单等辅助材料重复计入金额。
- 不得把无法读取或无法确认的材料排除在报告之外；统一列入待复核。

## 常见错误

| 错误 | 正确做法 |
| --- | --- |
| 整封综合发票邮件都归入一次差旅 | 逐个打开附件，核对每组日期、城市和金额 |
| PDF、XML、OFD 分别计费 | 按发票号、订单号和内容识别为同一计算项 |
| 邮箱不可用就终止任务 | 降级为本地材料模式并列出缺口 |
| 把外币与人民币实付同时计算 | 只计算报销口径对应金额，原币与汇率写入备注 |
| 用本地打车推断跨城票已齐全 | 本地交通只能作为推断依据，不能替代主要跨城票据 |
| 把个人档案打入分享包 | 档案始终保存在 Skill 目录之外 |
