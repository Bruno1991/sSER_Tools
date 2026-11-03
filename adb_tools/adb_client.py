"""Fachada de compatibilidade retroativa para adb_tools.adb_client."""

from ser_tools.android.adb_client import AdbClient, AdbDevice, AndroidDevice

__all__ = ["AdbClient", "AdbDevice", "AndroidDevice"]
