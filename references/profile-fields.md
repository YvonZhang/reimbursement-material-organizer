# 用户档案字段

## 保存位置

默认保存到：

```text
~/.codex/reimbursement-material-organizer/profile.json
```

设置 `REIMBURSEMENT_PROFILE_PATH` 可以覆盖位置。档案必须位于 Skill 安装目录之外。

覆盖路径必须是绝对路径。配置脚本会解析路径并拒绝 Skill 目录内部的目标，包括通过符号链接解析后落入 Skill 目录的路径。

## 首次配置问题

按以下顺序收集：

1. 报销人姓名。
2. 常用出行人，可为空。
3. 公司名称。
4. 发票抬头和税号，可为空。
5. 默认输出目录。
6. 邮箱类型：`auto`、`gmail`、`outlook`、`qiye-163`、`local-only` 或用户说明的其他类型。
7. 常用搜索文件夹，可为空。
8. 默认币种。
9. 报销分类；未指定时使用通用默认分类。
10. 自定义规则，可为空。
11. 公司预设：`none` 或 `hutong`。

不要询问或保存密码、Passphrase、访问令牌、刷新令牌、Cookie、API Key、授权头或客户端密钥。

## JSON 结构

```json
{
  "schema_version": 1,
  "profile_name": "default",
  "claimant": {
    "name": "示例用户",
    "travellers": ["示例用户"]
  },
  "organization": {
    "name": "示例公司",
    "invoice_title": "示例公司",
    "tax_id": ""
  },
  "storage": {
    "default_output_dir": "/path/to/reimbursements"
  },
  "mail": {
    "provider": "auto",
    "folders": []
  },
  "rules": {
    "base_currency": "CNY",
    "categories": ["酒店", "交通打车", "公共交通", "机票", "火车票", "其它"],
    "custom": [],
    "preset": "none"
  }
}
```

必填非空字段：

- `schema_version`，固定为 `1`
- `profile_name`
- `claimant.name`
- `organization.name`
- `storage.default_output_dir`
- `mail.provider`
- `rules.base_currency`
- `rules.categories`，至少包含一个非空字符串

档案采用严格字段白名单。未声明字段、类型错误、未知公司预设和任何疑似凭据字段都会导致校验失败。

## 创建与更新

1. 把用户回答写入任务临时目录中的 JSON。
2. 运行 `python3 scripts/profile_manager.py validate <文件>`。
3. 校验通过后运行 `python3 scripts/profile_manager.py save <文件>`。
4. 运行 `show` 展示已保存的非敏感摘要；税号默认显示为 `***已隐藏***`。
5. 更新时先读取现有档案，展示差异并确认，再运行 `save <文件> --force`。

不要在展示摘要时输出税号全文；默认只显示是否已配置。删除档案属于重置操作，必须由用户明确要求并精确确认目标路径。
