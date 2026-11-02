"""Testes unitários para o módulo FfdecManager e descompilação de SWF."""

import unittest
from pathlib import Path

from ser_tools.android.ffdec_manager import FfdecManager
from ser_tools.core.config import SuiteConfig


class TestFfdecManager(unittest.TestCase):
    def setUp(self):
        self.ffdec = FfdecManager()
        self.config = SuiteConfig()
        self.slither_swf = (
            self.config.decompiled_sources_dir / "air.com.hypah.io.slither" / "air_extracted" / "slither android.swf"
        )

    def test_ffdec_installed(self):
        self.assertTrue(self.ffdec.is_installed(), "FFDec deve estar instalado e reconhecido.")
        jar = self.ffdec.get_ffdec_jar()
        self.assertIsNotNone(jar)
        self.assertTrue(jar.is_file())
        self.assertEqual(jar.name, "ffdec.jar")

    def test_locate_swf(self):
        if not self.slither_swf.exists():
            # Tenta localizar qualquer arquivo .swf de teste existente
            swfs = list(self.config.decompiled_sources_dir.rglob("*.swf"))
            if swfs:
                self.slither_swf = swfs[0]
            else:
                self.skipTest("slither android.swf não encontrado em decompiled_sources.")

        # 1. Por caminho direto
        found = self.ffdec.locate_swf(str(self.slither_swf))
        self.assertIsNotNone(found)
        self.assertEqual(found.resolve(), self.slither_swf.resolve())

        # 2. Por nome do pacote
        found_pkg = self.ffdec.locate_swf("air.com.hypah.io.slither")
        if found_pkg:
            self.assertTrue(found_pkg.is_file())
            self.assertEqual(found_pkg.suffix.lower(), ".swf")


if __name__ == "__main__":
    unittest.main()
