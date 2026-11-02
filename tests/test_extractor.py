"""Testes unitários para o extrator de s_SER_Tools."""

import io
from pathlib import Path
import unittest
import zipfile

from ser_tools.android.adb_client import AdbClient, AndroidDevice
from ser_tools.core.config import SuiteConfig


class TestAdbTools(unittest.TestCase):
    def test_format_bytes(self):
        # Validação de formatação de bytes
        from adb_tools.cli import format_bytes
        self.assertEqual(format_bytes(500), "500.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(5 * 1024 * 1024), "5.00 MB")

    def test_resolve_adb_path_finds_platform_tools(self):
        resolved = AdbClient._resolve_adb_path()
        self.assertTrue(resolved.endswith("adb.exe") or resolved == "adb")
        self.assertTrue(Path(resolved).exists() or resolved == "adb")

    def test_extracted_apk_validity_if_present(self):
        config = SuiteConfig()
        candidates = list(config.extracted_apks_dir.rglob("*.apk"))
        if not candidates:
            self.skipTest("Nenhum APK extraído presente em extracted_apks.")

        apk_path = candidates[0]
        self.assertTrue(apk_path.stat().st_size > 10_000)
        with zipfile.ZipFile(apk_path, "r") as zf:
            self.assertIsNone(zf.testzip())


if __name__ == "__main__":
    unittest.main()
