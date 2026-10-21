import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scripts" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("build_release", MODULE_PATH)
build_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(build_release)


def minimal_skill_root(directory):
    root = Path(directory) / "reimbursement-material-organizer"
    root.mkdir()
    (root / "SKILL.md").write_text(
        "---\nname: reimbursement-material-organizer\n"
        "description: Use when testing.\n---\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Test\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    return root


class BuildReleaseTests(unittest.TestCase):
    def test_collect_release_files_includes_source_and_excludes_caches(self):
        resolved_root = ROOT.resolve()
        files = {
            path.relative_to(resolved_root).as_posix()
            for path in build_release.collect_release_files(ROOT)
        }
        self.assertIn("SKILL.md", files)
        self.assertIn("scripts/profile_manager.py", files)
        self.assertIn("scripts/build_release.py", files)
        self.assertFalse(any("__pycache__" in path for path in files))
        self.assertFalse(any(path.endswith(".pyc") for path in files))

    def test_build_creates_one_top_level_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release.zip"
            digest = build_release.build_release(ROOT, output)
            self.assertEqual(len(digest), 64)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
            self.assertTrue(names)
            self.assertEqual(
                {name.split("/", 1)[0] for name in names},
                {"reimbursement-material-organizer"},
            )
            self.assertFalse(any("__pycache__" in name for name in names))
            self.assertFalse(any(name.endswith(".pyc") for name in names))

    def test_build_is_byte_for_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            first_digest = build_release.build_release(ROOT, first)
            second_digest = build_release.build_release(ROOT, second)
            self.assertEqual(first_digest, second_digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_collect_rejects_profile_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = minimal_skill_root(directory)
            (root / "profile.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_release.collect_release_files(root)

    def test_collect_rejects_real_reimbursement_material(self):
        with tempfile.TemporaryDirectory() as directory:
            root = minimal_skill_root(directory)
            (root / "invoice.pdf").write_bytes(b"%PDF-test")
            with self.assertRaises(ValueError):
                build_release.collect_release_files(root)

    def test_collect_requires_open_source_root_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "reimbursement-material-organizer"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: reimbursement-material-organizer\n"
                "description: Use when testing.\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "missing required release files"):
                build_release.collect_release_files(root)

    def test_collect_rejects_personal_home_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = minimal_skill_root(directory)
            personal_path = "/" + "Users" + "/example/private"
            (root / "README.md").write_text(personal_path, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "personal home path"):
                build_release.collect_release_files(root)

    def test_collect_rejects_credential_pattern(self):
        with tempfile.TemporaryDirectory() as directory:
            root = minimal_skill_root(directory)
            credential = "sk-" + ("A" * 20)
            (root / "README.md").write_text(credential, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "credential-like value"):
                build_release.collect_release_files(root)

    def test_collect_rejects_symbolic_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = minimal_skill_root(directory)
            link = root / "linked-readme.md"
            try:
                link.symlink_to(root / "README.md")
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "symbolic links"):
                build_release.collect_release_files(root)

    def test_collect_rejects_unexpected_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = minimal_skill_root(directory)
            (root / "NOTES.txt").write_text("unexpected\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unexpected root file"):
                build_release.collect_release_files(root)

    def test_write_checksum_creates_companion_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release.zip"
            checksum = Path(directory) / "release.sha256"
            digest = build_release.build_release(ROOT, output)
            build_release.write_checksum(digest, output, checksum)
            self.assertEqual(
                checksum.read_text(encoding="utf-8"),
                f"{digest}  release.zip\n",
            )


if __name__ == "__main__":
    unittest.main()
