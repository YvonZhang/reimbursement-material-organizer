import importlib.util
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillPackageTests(unittest.TestCase):
    def test_required_skill_files_exist(self):
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/core-rules.md",
            "references/profile-fields.md",
            "references/output-spec.md",
            "references/presets/hutong.md",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_frontmatter_is_discoverable_and_has_no_placeholders(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: reimbursement-material-organizer", text)
        description = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
        self.assertIsNotNone(description)
        self.assertTrue(description.group(1).startswith("Use when"))
        self.assertNotRegex(text, r"\b(?:TODO|TBD)\b")

    def test_skill_contains_core_execution_contract(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("邮箱能力", text)
        self.assertIn("本地材料", text)
        self.assertIn("profile_manager.py", text)
        self.assertIn("本次任务 > 用户档案 > 公司预设 > 通用规则", text)
        self.assertIn("不得删除", text)
        self.assertIn("待复核", text)

    def test_generic_files_have_no_personal_absolute_path(self):
        personal_home_pattern = re.compile(r"/(?:Users|home)/[^/\s\"']+")
        for path in ROOT.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".yaml", ".py", ".json"}:
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(personal_home_pattern.search(text), str(path))

    def test_hutong_rules_are_isolated_to_preset(self):
        core = (ROOT / "references/core-rules.md").read_text(encoding="utf-8")
        preset = (ROOT / "references/presets/hutong.md").read_text(encoding="utf-8")
        self.assertNotIn("智慧互通", core)
        self.assertIn("智慧互通", preset)

    def test_skill_stays_within_progressive_disclosure_limit(self):
        lines = (ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), 500)

    def test_acceptance_rules_cover_fallback_dedup_currency_and_uncertainty(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        core = (ROOT / "references" / "core-rules.md").read_text(encoding="utf-8")
        output = (ROOT / "references" / "output-spec.md").read_text(encoding="utf-8")
        self.assertIn("不因为缺少邮箱工具而停止", skill)
        self.assertIn("本次任务 > 用户档案 > 公司预设 > 通用规则", skill)
        self.assertIn("同一发票的 PDF、XML、OFD 只计算一次", core)
        self.assertIn("CNY、HKD、USD、EUR 等币种分别小计", core)
        self.assertIn("金额：待复核", output)

    def test_open_source_metadata_and_user_guide(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        for phrase in [
            "Yvon Zhang",
            "MIT",
            "安装",
            "首次配置",
            "隐私",
            "智慧互通",
        ]:
            self.assertIn(phrase, readme)
        self.assertIn("Copyright (c) 2026 Yvon Zhang", license_text)
        self.assertIn("Permission is hereby granted", license_text)

    def test_readme_documents_checksum_and_repeatable_build(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("shasum -a 256 -c", readme)
        self.assertIn("build_release.py", readme)

    def test_example_profile_is_valid_and_fictional(self):
        module_path = ROOT / "scripts" / "profile_manager.py"
        spec = importlib.util.spec_from_file_location(
            "profile_manager_example", module_path
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        example_path = ROOT / "examples" / "profile.example.json"
        data = json.loads(example_path.read_text(encoding="utf-8"))
        self.assertEqual(module.validate_profile(data), [])
        self.assertIn("示例", example_path.read_text(encoding="utf-8"))

    def test_sample_requests_cover_generic_and_preset_usage(self):
        text = (ROOT / "examples" / "sample-request.md").read_text(encoding="utf-8")
        self.assertIn("通用模式", text)
        self.assertIn("智慧互通预设", text)

    def test_forward_test_results_record_behavioral_acceptance(self):
        text = (
            ROOT / "examples" / "acceptance-scenarios.md"
        ).read_text(encoding="utf-8")
        for phrase in [
            "无 Skill 基线",
            "通用模式",
            "智慧互通预设",
            "未创建空分类",
            "100.00 CNY",
            "本次任务 > 用户档案 > 公司预设 > 通用规则",
        ]:
            self.assertIn(phrase, text)

    def test_output_spec_confines_untrusted_names_to_output_root(self):
        text = (ROOT / "references" / "output-spec.md").read_text(encoding="utf-8")
        self.assertIn("basename", text)
        self.assertIn("路径必须位于输出根目录内", text)
        self.assertIn("不得跟随符号链接", text)
        self.assertIn("`..`", text)
        self.assertIn("待复核清单.txt", text)


if __name__ == "__main__":
    unittest.main()
