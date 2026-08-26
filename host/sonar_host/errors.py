class SonarHostError(Exception):
    """Base class for host-pipeline failures."""


class PacketFormatError(SonarHostError):
    """A capture packet violated the documented contract."""


class TruncatedPacketError(PacketFormatError):
    """A packet or stream ended before the contract allowed."""


class HeaderCRCError(PacketFormatError):
    """The SNP1 header CRC did not match."""


class PayloadCRCError(PacketFormatError):
    """The SNP1 payload CRC did not match."""


class StreamFormatError(SonarHostError):
    """The SNR1 streaming header violated the documented contract."""


class StreamIncompleteError(SonarHostError):
    """A continuous stream stopped before the caller's capture request completed."""


class StreamOverflowError(SonarHostError):
    """Hardware or the transport reported a sticky overflow condition."""


class CalibrationError(SonarHostError):
    """Calibration inputs were missing or malformed."""
