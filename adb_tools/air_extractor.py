"""Fachada de compatibilidade retroativa para adb_tools.air_extractor."""

from ser_tools.android.air_extractor import (
    AirAppInfo,
    AirExtractor,
    AirExtractorResult,
    SwfHeaderInfo,
    parse_swf_header,
)

__all__ = [
    "AirAppInfo",
    "AirExtractor",
    "AirExtractorResult",
    "SwfHeaderInfo",
    "parse_swf_header",
]
