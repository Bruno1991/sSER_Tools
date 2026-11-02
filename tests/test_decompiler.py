"""Testes unitários para o módulo de descompilação de s_SER_Tools."""

import unittest
from pathlib import Path

from ser_tools.android.decompiler import ApkDecompiler, JadxManager, JavaEnvironment
from ser_tools.core.config import SuiteConfig


class TestDecompiler(unittest.TestCase):
    def test_java_environment_resolution(self):
        java_home = JavaEnvironment.resolve_java_home()
        self.assertIsNotNone(java_home, "Java Runtime (JDK 17) deve ser resolvido.")
        java_exe = java_home / "bin" / ("java.exe" if Path().resolve().drive else "java")
        self.assertTrue(java_exe.is_file(), "java.exe deve existir.")

    def test_jadx_installation_and_binaries(self):
        jadx_mgr = JadxManager()
        self.assertTrue(jadx_mgr.is_installed(), "JADX deve estar instalado em tools/jadx.")
        cli = jadx_mgr.get_jadx_cli()
        gui = jadx_mgr.get_jadx_gui()
        self.assertIsNotNone(cli)
        self.assertIsNotNone(gui)
        self.assertTrue(cli.is_file())
        self.assertTrue(gui.is_file())

    def test_locate_apk(self):
        apk = (
            ApkDecompiler.locate_apk("com.chess")
            or ApkDecompiler.locate_apk("base")
            or ApkDecompiler.locate_apk("com.smartexpenditure")
        )
        if not apk:
            self.skipTest("Nenhum APK de teste localizado em extracted_apks.")
        self.assertTrue(apk.is_file())
        self.assertEqual(apk.suffix.lower(), ".apk")

    def test_decompiled_sources_structure(self):
        config = SuiteConfig()
        candidates = [
            config.decompiled_sources_dir / "com.chess",
            config.decompiled_sources_dir / "com.smartexpenditure",
        ]
        decomp_dir = next((d for d in candidates if d.is_dir()), None)
        if not decomp_dir:
            self.skipTest("Pasta de código descompilado não encontrada em decompiled_sources.")

        # Verificar AndroidManifest.xml (seja em app/src/main, resources ou raiz)
        manifest_paths = [
            decomp_dir / "resources" / "AndroidManifest.xml",
            decomp_dir / "app" / "src" / "main" / "AndroidManifest.xml",
            decomp_dir / "AndroidManifest.xml",
        ]
        manifest = next((m for m in manifest_paths if m.is_file()), None)
        self.assertIsNotNone(manifest, "AndroidManifest.xml deve existir e ser legível.")


if __name__ == "__main__":
    unittest.main()
