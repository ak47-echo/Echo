import tempfile
import unittest
from pathlib import Path

from portfolio_auto_import import run_portfolio_auto_import


class PortfolioAutoImportTests(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.downloads = self.root / "Downloads"
        self.imports = self.root / "imports"
        self.downloads.mkdir()

    def tearDown(self):

        self.temp_dir.cleanup()

    def _write_download(self, name, text):

        path = self.downloads / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_disabled_by_default(self):

        result = run_portfolio_auto_import(
            downloads_dir=self.downloads,
            import_dir=self.imports,
            enabled=False
        )
        self.assertEqual("disabled", result["status"])

    def test_copies_newest_matching_csv(self):

        old = self._write_download("All-Accounts-Positions-old.csv", "old")
        new = self._write_download("All-Accounts-Positions-new.csv", "new")
        old.touch()
        new.touch()
        result = run_portfolio_auto_import(
            downloads_dir=self.downloads,
            import_dir=self.imports,
            pattern="All-Accounts-Positions-*.csv",
            enabled=True
        )
        self.assertEqual("copied", result["status"])
        self.assertEqual("new", Path(result["copied_path"]).read_text())

    def test_already_imported_behavior(self):

        source = self._write_download("All-Accounts-Positions-test.csv", "same")
        self.imports.mkdir()
        (self.imports / source.name).write_text("same", encoding="utf-8")
        result = run_portfolio_auto_import(
            downloads_dir=self.downloads,
            import_dir=self.imports,
            enabled=True
        )
        self.assertEqual("already_imported", result["status"])

    def test_does_not_delete_downloads_file(self):

        source = self._write_download("All-Accounts-Positions-test.csv", "same")
        run_portfolio_auto_import(
            downloads_dir=self.downloads,
            import_dir=self.imports,
            enabled=True
        )
        self.assertTrue(source.exists())

    def test_filename_collision_handled_safely(self):

        source = self._write_download("All-Accounts-Positions-test.csv", "new")
        self.imports.mkdir()
        (self.imports / source.name).write_text("old", encoding="utf-8")
        result = run_portfolio_auto_import(
            downloads_dir=self.downloads,
            import_dir=self.imports,
            enabled=True
        )
        self.assertEqual("copied", result["status"])
        self.assertNotEqual(str(self.imports / source.name), result["copied_path"])


if __name__ == "__main__":
    unittest.main()
