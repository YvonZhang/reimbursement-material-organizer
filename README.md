# 通用报销材料整理 Skill

一个可分享、可配置的 Codex Skill：从已连接的邮箱或用户提供的本地文件收集差旅凭证，完成附件核验、分类、去重、分币种汇总、每日行程重建和缺票检查。

- 作者：Yvon Zhang
- 许可证：MIT
- 版本：1.0.0（源分享包；本仓库补充研究后的使用说明）

## 定位、输入和输出

这是供 Codex 读取的工作流 Skill。`SKILL.md` 与 `references/` 规定整理步骤；票据读取、邮箱搜索和文件归档由 Codex 使用当前可用工具完成。

输入包括差旅日期、城市或关键词、用户提供的本地凭证，以及可选的已连接邮箱。配置示例使用虚构姓名和公司；实际配置保存在 Skill 目录之外。

输出包括分类后的原件副本、各分类清单、逐币种金额、每日行程、`整理摘要.txt`、`检查.txt`，以及需要时生成的待复核清单。它不提交报销审批、不付款。

包内两个 Python 脚本仅负责：

| 文件 | 作用 |
| --- | --- |
| `scripts/profile_manager.py` | 校验、保存和显示本地用户档案，默认隐藏税号 |
| `scripts/build_release.py` | 按文件白名单生成可重复的 ZIP 和 SHA-256 校验文件 |

## 依赖与限制

- 需要能加载 Skill 的 Codex 环境；Python 脚本使用 Python 3.10 或更新版本，仅依赖标准库，没有 pip 安装步骤。
- 包内没有独立票据解析器、OCR 引擎或邮箱客户端。PDF、OFD、图片等是否能读取，取决于当前环境的工具；无法确认的内容列入待复核。
- 邮箱搜索必须使用用户已连接且匹配的工具；没有邮箱能力时可整理本地材料。
- 金额去重、归属判断和行程重建由代理依照规则执行，需要复核。币种分别汇总；没有明确依据时不自行换汇。
- `hutong` 是可选参考预设，不代表现行公司报销制度；使用者应按实际制度调整。
- 档案会在本地明文保存姓名、公司等配置；不要保存凭据。税号仅在默认显示摘要时遮蔽，存储本身没有加密。
- `--force` 会覆盖明确指定的档案或发布文件，请核对目标路径。发布扫描器采用有限模式匹配，不能替代人工敏感内容检查。
- 本次发布只做静态语法、结构、链接和敏感内容检查，没有运行包内脚本、单元测试、真实邮箱或真实报销流程。`examples/acceptance-scenarios.md` 是源包自带的场景记录。

## 能做什么

- 首次对话收集非敏感基础信息，之后重复使用。
- 自动检测可用邮箱能力；没有邮箱工具时继续处理本地材料。
- 保留 PDF、XML、OFD 和图片等有效原件，同一计算项只计一次。
- 分币种汇总，不擅自使用汇率。
- 生成分类清单、`整理摘要.txt` 和 `检查.txt`。
- 提供通用规则，以及独立可选的智慧互通预设。

## 安装

1. 如果分享包同时提供 `.sha256` 文件，先在两个文件所在目录验证：

   ```bash
   shasum -a 256 -c reimbursement-material-organizer-1.0.0.sha256
   ```

2. 解压分享包。
3. 确认解压后只有一个顶层目录 `reimbursement-material-organizer`。
4. 把该目录放入 Codex 的 Skills 目录：

   ```text
   ~/.codex/skills/reimbursement-material-organizer
   ```

   如果设置了 `CODEX_HOME`，使用其中的 `skills` 子目录。

5. 重新打开 Codex，或开始一个新任务，让新 Skill 被发现。

## 首次配置

在 Codex 中输入：

```text
使用 $reimbursement-material-organizer 帮我完成首次配置。
```

Skill 会询问报销人、公司、默认输出目录、邮箱类型、币种、分类、自定义规则和公司预设。发票抬头、税号与常用出行人均可选。

档案默认保存在：

```text
~/.codex/reimbursement-material-organizer/profile.json
```

它不在 Skill 安装目录内，因此更新或重新分享 Skill 时不会带出个人配置。

### 查看或更新档案

直接对 Codex 说：

```text
使用 $reimbursement-material-organizer 查看我的报销档案。
使用 $reimbursement-material-organizer 把默认输出目录改为……
```

更新前应先展示变更摘要，再覆盖原档案。

## 日常使用

最少提供差旅日期，以及城市或可用于搜索的关键词：

```text
使用 $reimbursement-material-organizer 整理 2026-06-10 至 2026-06-12 的上海差旅报销材料。
```

也可以补充本地材料目录、出行人、邮箱文件夹、特殊分类规则或更窄的搜索范围。

有匹配且已连接的邮箱能力时，Skill 只读搜索、读取和下载候选附件；没有邮箱能力或登录失败时，会转为本地材料模式并告诉你还缺什么。

## 智慧互通预设

首次配置时把公司预设设为 `hutong`，即可加载智慧互通常见的网易企业 163 邮箱文件夹、材料类型和分类经验。

该预设与通用规则分开。其他公司用户使用 `none`，不会加载智慧互通专属内容。

规则优先级：

```text
本次任务 > 用户档案 > 公司预设 > 通用规则
```

## 隐私与安全

- 不要向 Skill 提供邮箱密码、访问令牌、Cookie、API Key 或客户端密钥。
- 凭据由邮箱工具、连接器或系统钥匙串管理。
- 邮箱操作只限搜索、读取和下载附件；不会发送、转发、归档、删除或修改标签。
- 不删除、移动或覆盖原始本地材料。
- 个人档案、临时文件和真实发票不应放进 Skill 目录，也不会进入发布 ZIP。
- 税号可以保存，但展示档案摘要时默认不输出全文。

## 包结构

```text
reimbursement-material-organizer/
├── SKILL.md
├── README.md
├── LICENSE
├── agents/openai.yaml
├── scripts/
│   ├── profile_manager.py
│   └── build_release.py
├── references/
│   ├── core-rules.md
│   ├── profile-fields.md
│   ├── output-spec.md
│   └── presets/hutong.md
├── examples/
│   ├── profile.example.json
│   ├── sample-request.md
│   └── acceptance-scenarios.md
└── tests/
```

## 卸载

删除 Skills 目录中的 `reimbursement-material-organizer` 即可卸载 Skill。用户档案位于另一目录，不会自动删除；只有在确认不再需要时，才单独删除档案。

## 开源与贡献

本项目由 Yvon Zhang 以 MIT License 开源。你可以使用、修改、再发布和用于商业项目，但需要保留版权与许可声明。

提交改进时，请避免加入真实发票、邮箱地址、个人路径、公司内部凭据或个人档案。

源包 1.0.0 的打包器只接受白名单文件，会拒绝 Git 工作树中的 `.git/`、`.gitignore` 等额外文件。打包时先用 Git 导出干净源码，再从导出目录运行；以下命令在仓库根目录执行：

```bash
release_work="$(mktemp -d)"
git archive --format=tar --prefix=reimbursement-material-organizer/ HEAD | tar -xf - -C "$release_work"
# .gitignore 只用于 Git 工作树，不属于 Skill 发布包。
rm "$release_work/reimbursement-material-organizer/.gitignore"
cd "$release_work/reimbursement-material-organizer"
python3 scripts/build_release.py \
  --output ../reimbursement-material-organizer-1.0.0.zip \
  --checksum ../reimbursement-material-organizer-1.0.0.sha256
```

命令同时生成 ZIP 与配套 `.sha256` 文件。打包器只接受明确允许的源码与说明文件，拒绝个人档案、真实票据、符号链接、个人主目录路径和疑似凭据。
