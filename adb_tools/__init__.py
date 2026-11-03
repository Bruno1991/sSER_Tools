"""s_ADB_Tools Facade - Mantido para compatibilidade retroativa total com a suíte s_SER_Tools."""

from ser_tools.android.adb_client import AdbClient, AdbDevice, AndroidDevice
from ser_tools.android.air_extractor import AirAppInfo, AirExtractor, AirExtractorResult, parse_swf_header
from ser_tools.android.decompiler import ApkDecompiler, DecompileResult, JadxManager, JavaEnvironment
from ser_tools.android.extractor import ApkExtractor, ExtractedPackage
from ser_tools.android.ffdec_manager import FfdecExportResult, FfdecManager
from ser_tools.core.utils import format_bytes

__version__ = "3.0.0"

__all__ = [
    "AdbClient",
    "AdbDevice",
    "AndroidDevice",
    "AirAppInfo",
    "AirExtractor",
    "AirExtractorResult",
    "parse_swf_header",
    "ApkDecompiler",
    "DecompileResult",
    "JadxManager",
    "JavaEnvironment",
    "ApkExtractor",
    "ExtractedPackage",
    "FfdecExportResult",
    "FfdecManager",
    "format_bytes",
]
