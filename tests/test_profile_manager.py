import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "profile_manager.py"
SPEC = importlib.util.spec_from_file_location("profile_manager", MODULE_PATH)
profile_manager = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(profile_manager)


def valid_profile():
    return {
        "schema_version": 1,
        "profile_name": "default",
        "claimant": {"name": "示例用户", "travellers": ["示例用户"]},
        "organization": {
            "name": "示例公司",
            "invoice_title": "示例公司",
            "tax_id": "",
        },
        "storage": {"default_output_dir": "/tmp/reimbursements"},
        "mail": {"provider": "auto", "folders": []},
        "rules": {
            "base_currency": "CNY",
            "categories": [
                "酒店",
                "交通打车",
                "公共交通",
                "机票",
                "火车票",
                "其它",
            ],
            "custom": [],
            "preset": "none",
        },
    }


class ProfileManagerTests(unittest.TestCase):
    def test_valid_profile_has_no_errors(self):
        self.assertEqual(profile_manager.validate_profile(valid_profile()), [])

    def test_sensitive_key_is_rejected_recursively(self):
        profile = valid_profile()
        profile["mail"]["access_token"] = "do-not-save"
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("access_token" in error for error in errors))

    def test_sensitive_key_suffix_is_rejected(self):
        profile = valid_profile()
        profile["mail"]["smtp_password"] = "do-not-save"
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("smtp_password" in error for error in errors))

    def test_camel_case_sensitive_key_is_rejected(self):
        profile = valid_profile()
        profile["mail"]["oauthToken"] = "do-not-save"
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("oauthToken" in error for error in errors))

    def test_unknown_fields_are_rejected(self):
        profile = valid_profile()
        profile["credentials"] = {"client_secret_value": "do-not-save"}
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("unknown field: credentials" in error for error in errors))

    def test_documented_optional_fields_have_strict_types(self):
        profile = valid_profile()
        profile["claimant"]["travellers"] = "示例用户"
        profile["mail"]["folders"] = [123]
        profile["rules"]["custom"] = "不允许"
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("claimant.travellers" in error for error in errors))
        self.assertTrue(any("mail.folders" in error for error in errors))
        self.assertTrue(any("rules.custom" in error for error in errors))

    def test_preset_must_be_supported(self):
        profile = valid_profile()
        profile["rules"]["preset"] = "unknown-company"
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("rules.preset" in error for error in errors))

    def test_missing_required_value_is_rejected(self):
        profile = valid_profile()
        profile["claimant"]["name"] = ""
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("claimant.name" in error for error in errors))

    def test_categories_must_be_a_non_empty_string_list(self):
        profile = valid_profile()
        profile["rules"]["categories"] = []
        errors = profile_manager.validate_profile(profile)
        self.assertTrue(any("rules.categories" in error for error in errors))

    def test_save_round_trip_uses_private_file_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            saved = profile_manager.save_profile(valid_profile(), path)
            self.assertEqual(saved, path.resolve())
            self.assertEqual(profile_manager.load_profile(path), valid_profile())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_save_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            profile_manager.save_profile(valid_profile(), path)
            with self.assertRaises(FileExistsError):
                profile_manager.save_profile(valid_profile(), path)

    def test_atomic_publish_refuses_target_created_during_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            with mock.patch.object(
                profile_manager.os,
                "link",
                side_effect=FileExistsError("simulated race"),
            ):
                with self.assertRaises(FileExistsError):
                    profile_manager.save_profile(valid_profile(), path)
            self.assertFalse(path.exists())

    def test_default_path_honours_environment_override(self):
        with mock.patch.dict(
            os.environ,
            {"REIMBURSEMENT_PROFILE_PATH": "~/custom-reimbursement-profile.json"},
        ):
            self.assertEqual(
                profile_manager.default_profile_path(),
                Path("~/custom-reimbursement-profile.json").expanduser(),
            )

    def test_relative_profile_path_is_rejected(self):
        with self.assertRaises(ValueError):
            profile_manager.resolve_profile_path(Path("profile.json"))

    def test_profile_path_inside_skill_is_rejected(self):
        skill_root = MODULE_PATH.parents[1]
        with self.assertRaises(ValueError):
            profile_manager.resolve_profile_path(skill_root / "profile.json")

    def test_profile_summary_redacts_tax_id_without_mutating_profile(self):
        profile = valid_profile()
        profile["organization"]["tax_id"] = "91310000EXAMPLE"
        summary = profile_manager.profile_summary(profile)
        self.assertEqual(summary["organization"]["tax_id"], "***已隐藏***")
        self.assertEqual(profile["organization"]["tax_id"], "91310000EXAMPLE")


if __name__ == "__main__":
    unittest.main()
