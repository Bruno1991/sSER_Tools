"""Testes unitários para o módulo ser_tools.core.utils."""

from pathlib import Path
import tempfile
import unittest

from ser_tools.core.utils import calculate_sha256, format_bytes, sanitize_target_name


class TestCoreUtils(unittest.TestCase):
    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0.00 B")
        self.assertEqual(format_bytes(512), "512.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1536), "1.50 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1024), "1.00 TB")

    def test_calculate_sha256(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"s_SER_Tools_Test_Payload")
            temp_path = Path(f.name)

        try:
            # echo -n "s_SER_Tools_Test_Payload" | sha256sum
            # 2e264...
            sha = calculate_sha256(temp_path)
            self.assertEqual(len(sha), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in sha))
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_sanitize_target_name(self):
        self.assertEqual(sanitize_target_name("com.chess"), "com.chess")
        self.assertEqual(sanitize_target_name("com.app/sub:path"), "com.app_sub_path")
        self.assertEqual(sanitize_target_name("   "), "unnamed_target")
        self.assertEqual(sanitize_target_name("air.game-v1.0"), "air.game-v1.0")


if __name__ == "__main__":
    unittest.main()

