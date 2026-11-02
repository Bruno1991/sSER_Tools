"""
Testes de validação da engenharia reversa e análise estática do aplicativo Chess.com (com.chess).
"""

import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from ser_tools.core.config import SuiteConfig
from ser_tools.desktop_bin.checksec import ChecksecScanner


class TestChessAnalysis(unittest.TestCase):
    def setUp(self):
        self.config = SuiteConfig()
        self.chess_extracted_dir = self.config.extracted_apks_dir / "com.chess"
        self.base_apk = self.chess_extracted_dir / "base.apk"
        self.arm64_apk = self.chess_extracted_dir / "split_config.arm64_v8a.apk"
        self.decompiled_manifest = (
            self.config.decompiled_sources_dir / "com.chess" / "resources" / "AndroidManifest.xml"
        )

    def test_chess_apks_extracted(self):
        """Valida que todos os pacotes APK (base + splits) do Chess.com foram extraídos com integridade."""
        self.assertTrue(self.chess_extracted_dir.is_dir(), "Diretório de extração com.chess deve existir")
        self.assertTrue(self.base_apk.is_file(), "base.apk deve existir")
        self.assertTrue(self.arm64_apk.is_file(), "split_config.arm64_v8a.apk deve existir")

        # Verifica integridade do base.apk
        self.assertGreater(self.base_apk.stat().st_size, 100_000_000, "base.apk deve ter mais de 100MB")
        with zipfile.ZipFile(self.base_apk, "r") as zf:
            self.assertIsNone(zf.testzip(), "base.apk deve ser um arquivo ZIP integro")
            names = zf.namelist()
            self.assertIn("classes.dex", names)
            self.assertIn("classes2.dex", names)
            self.assertIn("AndroidManifest.xml", names)
            self.assertIn("assets/index.android.bundle", names)

    def test_chess_react_native_hermes_bundle(self):
        """Valida que a interface utiliza React Native pré-compilada em Hermes Bytecode (HBC)."""
        with zipfile.ZipFile(self.base_apk, "r") as zf:
            bundle_bytes = zf.read("assets/index.android.bundle")
            self.assertGreater(len(bundle_bytes), 1_000_000, "Bundle JS deve ter mais de 1MB")

            # Magic number do Hermes Bytecode (0x1FBC1FC6 -> b'\xc6\x1f\xbc\x03')
            hbc_magic = b"\xc6\x1f\xbc\x03"
            self.assertTrue(bundle_bytes.startswith(hbc_magic), "Bundle JS deve ser Hermes Bytecode (HBC)")

    def test_chess_native_libraries_and_cee(self):
        """Valida a presença do motor de xadrez nativo C++ (CEE / Stockfish) e do módulo Approov."""
        with zipfile.ZipFile(self.arm64_apk, "r") as zf:
            names = zf.namelist()
            self.assertIn("lib/arm64-v8a/libcee.so", names, "Chess Evaluation Engine nativo deve estar presente")
            self.assertIn("lib/arm64-v8a/libapproov.so", names, "Módulo de segurança Approov deve estar presente")
            self.assertIn("lib/arm64-v8a/libreactnative.so", names, "Runtime React Native deve estar presente")
            self.assertIn("lib/arm64-v8a/libhermesvm.so", names, "Hermes VM nativa deve estar presente")

            # Verifica tamanho do libcee.so (> 40MB descompactado)
            info_cee = zf.getinfo("lib/arm64-v8a/libcee.so")
            self.assertGreater(info_cee.file_size, 40_000_000, "Engine CEE nativa deve ser um binário completo")

    def test_chess_checksec_mitigations(self):
        """Executa Checksec nas bibliotecas nativas de Chess.com comprovando mitigações de segurança."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            with zipfile.ZipFile(self.arm64_apk, "r") as zf:
                lib_bytes = zf.read("lib/arm64-v8a/libcee.so")
                cee_so = tmp_path / "libcee.so"
                cee_so.write_bytes(lib_bytes)

                res = ChecksecScanner.scan(cee_so)
                self.assertEqual(res.binary_format, "ELF (Linux/Android)")
                self.assertEqual(res.architecture, "ELF64")
                self.assertEqual(res.overall_score, 100)

                mitigations_map = {m.name: m for m in res.mitigations}
                self.assertTrue(mitigations_map["PIE"].enabled, "PIE deve estar habilitado")
                self.assertTrue(mitigations_map["NX (No-Execute)"].enabled, "NX deve estar habilitado")
                self.assertTrue(mitigations_map["Stack Canary"].enabled, "Stack Canary deve estar habilitado")

    def test_chess_decompiled_manifest(self):
        """Valida a estrutura do AndroidManifest descompilado pelo JADX."""
        if not self.decompiled_manifest.is_file():
            self.skipTest("AndroidManifest descompilado ainda não disponível.")

        tree = ET.parse(self.decompiled_manifest)
        root = tree.getroot()
        self.assertEqual(root.attrib.get("package"), "com.chess")

        uses_sdk = root.find("uses-sdk")
        self.assertIsNotNone(uses_sdk)
        min_sdk = int(uses_sdk.attrib.get("{http://schemas.android.com/apk/res/android}minSdkVersion", 0))
        self.assertGreaterEqual(min_sdk, 21)

        # Checa presença de activities críticas
        app = root.find("application")
        self.assertIsNotNone(app)
        activities = [
            act.attrib.get("{http://schemas.android.com/apk/res/android}name", "")
            for act in app.findall("activity")
        ]
        self.assertTrue(any("SplashActivity" in a for a in activities))
        self.assertTrue(any("HomeActivity" in a for a in activities))


if __name__ == "__main__":
    unittest.main()

