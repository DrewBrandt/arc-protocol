"""Typed payload helpers for ARC control-plane message families."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from . import protocol
from . import messages_generated as _gen


class MessageError(ValueError):
    """Raised when a message payload is malformed."""


class NetMgmtType(IntEnum):
    HEARTBEAT = protocol.NETMGMT_HEARTBEAT
    ACK = protocol.NETMGMT_ACK
    SESSION_RESET = protocol.NETMGMT_SESSION_RESET
    BEACON = protocol.NETMGMT_BEACON


# Superframe MAC beacon. Generated; re-exported here as public API.
Beacon = _gen.Beacon


class VideoType(IntEnum):
    START_STREAM = 0x01
    STOP_STREAM = 0x02
    HARD_STOP = 0x03
    SET_BITRATE = 0x04
    GET_INFO = 0x05
    STATUS_REPORT = 0x10
    INFO_REPORT = 0x11


class FcVideoType(IntEnum):
    SET_LAYOUT = 0x01
    SET_SOURCE = 0x02
    SET_OVERLAY = 0x03
    GET_STATUS = 0x04
    GET_LAYOUTS = 0x05
    STATUS_REPORT = 0x10
    LAYOUTS_REPORT = 0x11


FcCoordType = _gen.FcCoordType

FC_COORD_STAGE_UNKNOWN = _gen.FC_COORD_STAGE_UNKNOWN
FC_COORD_STAGE_PAD = _gen.FC_COORD_STAGE_PAD
FC_COORD_STAGE_BOOST = _gen.FC_COORD_STAGE_BOOST
FC_COORD_STAGE_COAST = _gen.FC_COORD_STAGE_COAST
FC_COORD_STAGE_DROGUE = _gen.FC_COORD_STAGE_DROGUE
FC_COORD_STAGE_MAIN = _gen.FC_COORD_STAGE_MAIN
FC_COORD_STAGE_LANDED = _gen.FC_COORD_STAGE_LANDED

FC_COORD_GPS_FIX_NONE = _gen.FC_COORD_GPS_FIX_NONE
FC_COORD_GPS_FIX_2D = _gen.FC_COORD_GPS_FIX_2D
FC_COORD_GPS_FIX_3D = _gen.FC_COORD_GPS_FIX_3D
FC_COORD_GPS_FIX_DGPS = _gen.FC_COORD_GPS_FIX_DGPS
FC_COORD_GPS_FIX_RTK_FLOAT = _gen.FC_COORD_GPS_FIX_RTK_FLOAT
FC_COORD_GPS_FIX_RTK_FIXED = _gen.FC_COORD_GPS_FIX_RTK_FIXED

FlightTelemetry = _gen.FlightTelemetry
AirbrakeTelemetry = _gen.AirbrakeTelemetry
PayloadTelemetry = _gen.PayloadTelemetry
SetAirbrakeAngle = _gen.SetAirbrakeAngle


class RadioType(IntEnum):
    SET_FREQUENCY = 0x01
    SET_TX_POWER = 0x02
    GET_STATUS = 0x03
    SET_PHY_PROFILE = 0x04
    START_HOPPING = 0x05
    DATA_DOWNLINK = 0x06
    STATUS_REPORT = 0x10


# RadioStatusReport.error_flags bits.
RADIO_ERR_TX_BUSY = 0x01
RADIO_ERR_PLL_UNLOCK = 0x02
RADIO_ERR_OVERTEMP = 0x04
RADIO_ERR_RX_OVERRUN = 0x08

# Known RADIO SET_PHY_PROFILE profile ids. These are safer than exposing raw
# arbitrary PHY knobs for first-light and flight ops.
RADIO_PHY_PROFILE_SAFE_BW125 = 0x00
RADIO_PHY_PROFILE_FAST_BW500 = 0x01


class PowerType(IntEnum):
    SET_OUTPUT = 0x01
    SET_OUTPUT_MASK = 0x02
    GET_STATUS = 0x03
    STATUS_REPORT = 0x10
    BOARD_TELEMETRY = 0x11


# PowerSetOutput.state and PowerChannelStatus.state values.
POWER_OFF = 0x00
POWER_ON = 0x01

# PowerChannelStatus.state may also OR these fault bits in.
POWER_CHAN_FAULT_OVERCURRENT = 0x40
POWER_CHAN_FAULT_THERMAL = 0x80
POWER_CHAN_FAULT_MASK = POWER_CHAN_FAULT_OVERCURRENT | POWER_CHAN_FAULT_THERMAL

# Mirrors arc_messages_power.h's compile-time cap.
POWER_MAX_CHANNELS = 8

# PowerBoardTelemetry.charge_status values.
POWER_CHARGE_UNPLUGGED = 0x00
POWER_CHARGE_PLUGGED = 0x01
POWER_CHARGE_CHARGING = 0x02
POWER_CHARGE_FAULT = 0x03


# FcVideoStatusReport.sender_flags bits.
FC_VIDEO_STATUS_FLAG_ONLINE = 0x01
FC_VIDEO_STATUS_FLAG_TRANSMITTING = 0x02
FC_VIDEO_STATUS_FLAG_RECORDING = 0x04
FC_VIDEO_STATUS_FLAGS_MASK = (
    FC_VIDEO_STATUS_FLAG_ONLINE
    | FC_VIDEO_STATUS_FLAG_TRANSMITTING
    | FC_VIDEO_STATUS_FLAG_RECORDING
)


@dataclass(frozen=True)
class Ack:
    seq: int

    def encode(self) -> bytes:
        return _u16(self.seq, "seq").to_bytes(2, "big")

    @classmethod
    def decode(cls, payload: bytes) -> "Ack":
        _require_len(payload, 2, "ACK")
        return cls(seq=int.from_bytes(payload, "big"))


@dataclass(frozen=True)
class SetBitrate:
    bitrate_bps: int

    def encode(self) -> bytes:
        return _u32(self.bitrate_bps, "bitrate_bps").to_bytes(4, "big")

    @classmethod
    def decode(cls, payload: bytes) -> "SetBitrate":
        _require_len(payload, 4, "SET_BITRATE")
        return cls(bitrate_bps=int.from_bytes(payload, "big"))


@dataclass(frozen=True)
class StatusReport:
    state: int
    cpu_temp_c: int
    cpu_load_pct: int
    free_disk_mb: int
    rssi_dbm: int
    tx_frames: int
    dropped_frames: int

    def encode(self) -> bytes:
        return bytes(
            (
                _u8(self.state, "state"),
                _u8(self.cpu_temp_c, "cpu_temp_c"),
                _u8(self.cpu_load_pct, "cpu_load_pct"),
            )
        ) + b"".join(
            (
                _u16(self.free_disk_mb, "free_disk_mb").to_bytes(2, "big"),
                _i8(self.rssi_dbm, "rssi_dbm").to_bytes(1, "big", signed=True),
                _u16(self.tx_frames, "tx_frames").to_bytes(2, "big"),
                _u16(self.dropped_frames, "dropped_frames").to_bytes(2, "big"),
            )
        )

    @classmethod
    def decode(cls, payload: bytes) -> "StatusReport":
        _require_len(payload, 10, "STATUS_REPORT")
        return cls(
            state=payload[0],
            cpu_temp_c=payload[1],
            cpu_load_pct=payload[2],
            free_disk_mb=int.from_bytes(payload[3:5], "big"),
            rssi_dbm=int.from_bytes(payload[5:6], "big", signed=True),
            tx_frames=int.from_bytes(payload[6:8], "big"),
            dropped_frames=int.from_bytes(payload[8:10], "big"),
        )


@dataclass(frozen=True)
class VideoInfoReport:
    """A Sender's reply to VIDEO GET_INFO.

    Lets the Controller learn a Sender's human-friendly name (and which
    flight computer it is paired with, if any) at discovery time instead
    of pre-declaring it in controller config. A Sender is otherwise
    identified by its fixed ARC address; this carries the descriptive
    bits that don't fit in an address.

    Wire layout:
      [paired_fc u8]   (0x00 = ADDR_UNASSIGNED = no paired FC)
      [name UTF-8 + NUL]
    """

    name: str
    paired_fc: int = protocol.ADDR_UNASSIGNED

    def encode(self) -> bytes:
        raw = self.name.encode("utf-8")
        if b"\x00" in raw:
            raise MessageError("sender name must not contain a NUL byte")
        out = bytearray()
        out.append(_u8(self.paired_fc, "paired_fc"))
        out += raw
        out.append(0)
        if len(out) > protocol.MAX_PAYLOAD_SIZE:
            raise MessageError(
                "VIDEO INFO_REPORT payload exceeds maximum ARC payload size"
            )
        return bytes(out)

    @classmethod
    def decode(cls, payload: bytes) -> "VideoInfoReport":
        if len(payload) < 2:
            raise MessageError("VIDEO INFO_REPORT payload truncated")
        if not payload.endswith(b"\x00"):
            raise MessageError("VIDEO INFO_REPORT name must be null-terminated")
        try:
            name = payload[1:-1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MessageError("VIDEO INFO_REPORT name must be valid UTF-8") from exc
        return cls(name=name, paired_fc=payload[0])


@dataclass(frozen=True)
class SetLayout:
    layout_id: int

    def encode(self) -> bytes:
        return bytes((_u8(self.layout_id, "layout_id"),))

    @classmethod
    def decode(cls, payload: bytes) -> "SetLayout":
        _require_len(payload, 1, "SET_LAYOUT")
        return cls(layout_id=payload[0])


@dataclass(frozen=True)
class SetSource:
    slot_id: int
    sender_addr: int

    def encode(self) -> bytes:
        return bytes(
            (
                _u8(self.slot_id, "slot_id"),
                _u8(self.sender_addr, "sender_addr"),
            )
        )

    @classmethod
    def decode(cls, payload: bytes) -> "SetSource":
        _require_len(payload, 2, "SET_SOURCE")
        return cls(slot_id=payload[0], sender_addr=payload[1])


@dataclass(frozen=True)
class SetOverlay:
    text: str

    def encode(self) -> bytes:
        raw = self.text.encode("utf-8") + b"\x00"
        if len(raw) > protocol.MAX_PAYLOAD_SIZE:
            raise MessageError("SET_OVERLAY payload exceeds maximum ARC payload size")
        return raw

    @classmethod
    def decode(cls, payload: bytes) -> "SetOverlay":
        if not payload.endswith(b"\x00"):
            raise MessageError("SET_OVERLAY payload must be null-terminated")
        try:
            text = payload[:-1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MessageError("SET_OVERLAY payload must be valid UTF-8") from exc
        return cls(text=text)


@dataclass(frozen=True)
class FcVideoSenderStatus:
    addr: int
    flags: int


@dataclass(frozen=True)
class FcVideoStatusReport:
    """Controller's reply to FC_VIDEO GET_STATUS.

    Mirrors arc_messages_fc_video.h ``arc_fc_video_status_report_t``.
    """

    slots: tuple[int, ...]
    senders: tuple[FcVideoSenderStatus, ...]

    def encode(self) -> bytes:
        if len(self.slots) > 0xFF:
            raise MessageError("FcVideoStatusReport supports at most 255 slots")
        if len(self.senders) > 0xFF:
            raise MessageError("FcVideoStatusReport supports at most 255 senders")
        out = bytearray()
        out.append(len(self.slots))
        for slot in self.slots:
            out.append(_u8(slot, "slot"))
        out.append(len(self.senders))
        for sender in self.senders:
            if sender.flags & ~FC_VIDEO_STATUS_FLAGS_MASK:
                raise MessageError(
                    f"sender flags 0x{sender.flags:02x} include reserved bits"
                )
            out.append(_u8(sender.addr, "sender_addr"))
            out.append(_u8(sender.flags, "sender_flags"))
        if len(out) > protocol.MAX_PAYLOAD_SIZE:
            raise MessageError(
                "FcVideoStatusReport payload exceeds maximum ARC payload size"
            )
        return bytes(out)

    @classmethod
    def decode(cls, payload: bytes) -> "FcVideoStatusReport":
        if len(payload) < 2:
            raise MessageError("FcVideoStatusReport payload truncated")
        slot_count = payload[0]
        sender_count_offset = 1 + slot_count
        if len(payload) < sender_count_offset + 1:
            raise MessageError("FcVideoStatusReport payload truncated")
        slots = tuple(payload[1 : 1 + slot_count])
        sender_count = payload[sender_count_offset]
        body_offset = sender_count_offset + 1
        expected_len = body_offset + sender_count * 2
        if len(payload) != expected_len:
            raise MessageError("FcVideoStatusReport payload length mismatch")
        senders = tuple(
            FcVideoSenderStatus(
                addr=payload[body_offset + i * 2],
                flags=payload[body_offset + i * 2 + 1],
            )
            for i in range(sender_count)
        )
        return cls(slots=slots, senders=senders)


@dataclass(frozen=True)
class LayoutsReport:
    """Controller's reply to FC_VIDEO GET_LAYOUTS.

    Reports the Controller's configured layouts in order, so a ground tool can
    map a 1-byte ``layout_id`` (its index here) to a human name.

    Wire layout:
      [layout_count u8]
      [name UTF-8 + NUL] * layout_count
    """

    names: tuple[str, ...]

    def encode(self) -> bytes:
        if len(self.names) > 0xFF:
            raise MessageError("LayoutsReport supports at most 255 layouts")
        out = bytearray()
        out.append(len(self.names))
        for name in self.names:
            raw = name.encode("utf-8")
            if b"\x00" in raw:
                raise MessageError("layout name must not contain a NUL byte")
            out += raw
            out.append(0)
        if len(out) > protocol.MAX_PAYLOAD_SIZE:
            raise MessageError("LayoutsReport payload exceeds maximum ARC payload size")
        return bytes(out)

    @classmethod
    def decode(cls, payload: bytes) -> "LayoutsReport":
        if len(payload) < 1:
            raise MessageError("LayoutsReport payload truncated")
        count = payload[0]
        names: list[str] = []
        offset = 1
        for _ in range(count):
            end = payload.find(b"\x00", offset)
            if end < 0:
                raise MessageError("LayoutsReport name is not NUL-terminated")
            try:
                names.append(payload[offset:end].decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise MessageError("layout name must be valid UTF-8") from exc
            offset = end + 1
        if offset != len(payload):
            raise MessageError("LayoutsReport payload length mismatch")
        return cls(names=tuple(names))


@dataclass(frozen=True)
class RadioSetFrequency:
    frequency_hz: int

    def encode(self) -> bytes:
        return _u32(self.frequency_hz, "frequency_hz").to_bytes(4, "big")

    @classmethod
    def decode(cls, payload: bytes) -> "RadioSetFrequency":
        _require_len(payload, 4, "RADIO SET_FREQUENCY")
        return cls(frequency_hz=int.from_bytes(payload, "big"))


@dataclass(frozen=True)
class RadioSetTxPower:
    tx_power_dbm: int

    def encode(self) -> bytes:
        return _i8(self.tx_power_dbm, "tx_power_dbm").to_bytes(1, "big", signed=True)

    @classmethod
    def decode(cls, payload: bytes) -> "RadioSetTxPower":
        _require_len(payload, 1, "RADIO SET_TX_POWER")
        return cls(tx_power_dbm=int.from_bytes(payload, "big", signed=True))


@dataclass(frozen=True)
class RadioSetPhyProfile:
    profile_id: int

    def encode(self) -> bytes:
        return _u8(self.profile_id, "profile_id").to_bytes(1, "big")

    @classmethod
    def decode(cls, payload: bytes) -> "RadioSetPhyProfile":
        _require_len(payload, 1, "RADIO SET_PHY_PROFILE")
        return cls(profile_id=payload[0])


@dataclass(frozen=True)
class RadioStatusReport:
    """Mirrors arc_messages_radio.h ``arc_radio_status_report_t``."""

    frequency_hz: int
    tx_power_dbm: int
    rssi_dbm: int
    snr_db: int
    error_flags: int
    packets_rx: int
    packets_tx: int

    def encode(self) -> bytes:
        return b"".join((
            _u32(self.frequency_hz, "frequency_hz").to_bytes(4, "big"),
            _i8(self.tx_power_dbm, "tx_power_dbm").to_bytes(1, "big", signed=True),
            _i8(self.rssi_dbm, "rssi_dbm").to_bytes(1, "big", signed=True),
            _i8(self.snr_db, "snr_db").to_bytes(1, "big", signed=True),
            bytes((_u8(self.error_flags, "error_flags"),)),
            _u16(self.packets_rx, "packets_rx").to_bytes(2, "big"),
            _u16(self.packets_tx, "packets_tx").to_bytes(2, "big"),
        ))

    @classmethod
    def decode(cls, payload: bytes) -> "RadioStatusReport":
        _require_len(payload, 12, "RADIO STATUS_REPORT")
        return cls(
            frequency_hz=int.from_bytes(payload[0:4], "big"),
            tx_power_dbm=int.from_bytes(payload[4:5], "big", signed=True),
            rssi_dbm=int.from_bytes(payload[5:6], "big", signed=True),
            snr_db=int.from_bytes(payload[6:7], "big", signed=True),
            error_flags=payload[7],
            packets_rx=int.from_bytes(payload[8:10], "big"),
            packets_tx=int.from_bytes(payload[10:12], "big"),
        )


@dataclass(frozen=True)
class PowerSetOutput:
    channel: int
    state: int

    def encode(self) -> bytes:
        if self.state not in (POWER_OFF, POWER_ON):
            raise MessageError(
                f"POWER SET_OUTPUT state must be OFF (0x00) or ON (0x01), got 0x{self.state:02x}"
            )
        return bytes((_u8(self.channel, "channel"), _u8(self.state, "state")))

    @classmethod
    def decode(cls, payload: bytes) -> "PowerSetOutput":
        _require_len(payload, 2, "POWER SET_OUTPUT")
        return cls(channel=payload[0], state=payload[1])


@dataclass(frozen=True)
class PowerSetOutputMask:
    enable_mask: int
    state_mask: int

    def encode(self) -> bytes:
        return bytes((
            _u8(self.enable_mask, "enable_mask"),
            _u8(self.state_mask, "state_mask"),
        ))

    @classmethod
    def decode(cls, payload: bytes) -> "PowerSetOutputMask":
        _require_len(payload, 2, "POWER SET_OUTPUT_MASK")
        return cls(enable_mask=payload[0], state_mask=payload[1])


@dataclass(frozen=True)
class PowerChannelStatus:
    state: int
    current_ma: int


@dataclass(frozen=True)
class PowerStatusReport:
    """Mirrors arc_messages_power.h ``arc_power_status_report_t``."""

    channels: tuple[PowerChannelStatus, ...]
    bus_voltage_mv: int
    temp_c: int

    def encode(self) -> bytes:
        if len(self.channels) > POWER_MAX_CHANNELS:
            raise MessageError(
                f"POWER STATUS_REPORT supports at most {POWER_MAX_CHANNELS} channels"
            )
        out = bytearray()
        out.append(len(self.channels))
        for ch in self.channels:
            out.append(_u8(ch.state, "channel state"))
            out += _u16(ch.current_ma, "current_ma").to_bytes(2, "big")
        out += _u16(self.bus_voltage_mv, "bus_voltage_mv").to_bytes(2, "big")
        out.append(_i8(self.temp_c, "temp_c") & 0xFF)
        if len(out) > protocol.MAX_PAYLOAD_SIZE:
            raise MessageError(
                "POWER STATUS_REPORT payload exceeds maximum ARC payload size"
            )
        return bytes(out)

    @classmethod
    def decode(cls, payload: bytes) -> "PowerStatusReport":
        if len(payload) < 4:
            raise MessageError("POWER STATUS_REPORT payload truncated")
        channel_count = payload[0]
        if channel_count > POWER_MAX_CHANNELS:
            raise MessageError(
                f"POWER STATUS_REPORT channel_count={channel_count} exceeds cap {POWER_MAX_CHANNELS}"
            )
        expected = 1 + channel_count * 3 + 3
        if len(payload) != expected:
            raise MessageError("POWER STATUS_REPORT payload length mismatch")
        channels = tuple(
            PowerChannelStatus(
                state=payload[1 + i * 3],
                current_ma=int.from_bytes(payload[2 + i * 3 : 4 + i * 3], "big"),
            )
            for i in range(channel_count)
        )
        bus_off = 1 + channel_count * 3
        return cls(
            channels=channels,
            bus_voltage_mv=int.from_bytes(payload[bus_off : bus_off + 2], "big"),
            temp_c=int.from_bytes(payload[bus_off + 2 : bus_off + 3], "big", signed=True),
        )


@dataclass(frozen=True)
class PowerBoardTelemetry:
    output_on_mask: int
    output_fault_mask: int
    battery_voltage_mv: int
    charge_status: int
    charge_voltage_mv: int

    def encode(self) -> bytes:
        return b"".join((
            bytes((
                _u8(self.output_on_mask, "output_on_mask"),
                _u8(self.output_fault_mask, "output_fault_mask"),
            )),
            _u16(self.battery_voltage_mv, "battery_voltage_mv").to_bytes(2, "big"),
            bytes((_u8(self.charge_status, "charge_status"),)),
            _u16(self.charge_voltage_mv, "charge_voltage_mv").to_bytes(2, "big"),
        ))

    @classmethod
    def decode(cls, payload: bytes) -> "PowerBoardTelemetry":
        _require_len(payload, 7, "POWER BOARD_TELEMETRY")
        return cls(
            output_on_mask=payload[0],
            output_fault_mask=payload[1],
            battery_voltage_mv=int.from_bytes(payload[2:4], "big"),
            charge_status=payload[4],
            charge_voltage_mv=int.from_bytes(payload[5:7], "big"),
        )


def decode_netmgmt(type: int, payload: bytes) -> object | None:
    msg_type = NetMgmtType(type)
    if msg_type is NetMgmtType.ACK:
        return Ack.decode(payload)
    if msg_type is NetMgmtType.BEACON:
        return Beacon.decode(payload)
    _require_empty(payload, msg_type.name)
    return None


def decode_video(type: int, payload: bytes) -> object | None:
    msg_type = VideoType(type)
    if msg_type is VideoType.SET_BITRATE:
        return SetBitrate.decode(payload)
    if msg_type is VideoType.STATUS_REPORT:
        return StatusReport.decode(payload)
    if msg_type is VideoType.INFO_REPORT:
        return VideoInfoReport.decode(payload)
    _require_empty(payload, msg_type.name)
    return None


def decode_fc_video(type: int, payload: bytes) -> object | None:
    msg_type = FcVideoType(type)
    if msg_type is FcVideoType.SET_LAYOUT:
        return SetLayout.decode(payload)
    if msg_type is FcVideoType.SET_SOURCE:
        return SetSource.decode(payload)
    if msg_type is FcVideoType.SET_OVERLAY:
        return SetOverlay.decode(payload)
    if msg_type is FcVideoType.STATUS_REPORT:
        return FcVideoStatusReport.decode(payload)
    if msg_type is FcVideoType.LAYOUTS_REPORT:
        return LayoutsReport.decode(payload)
    _require_empty(payload, msg_type.name)
    return None


def decode_fc_coord(type: int, payload: bytes) -> object | None:
    try:
        return _gen.decode_fc_coord(type, payload)
    except _gen.MessageError as exc:
        raise MessageError(str(exc)) from exc


def decode_radio(type: int, payload: bytes) -> object | None:
    msg_type = RadioType(type)
    if msg_type is RadioType.SET_FREQUENCY:
        return RadioSetFrequency.decode(payload)
    if msg_type is RadioType.SET_TX_POWER:
        return RadioSetTxPower.decode(payload)
    if msg_type is RadioType.SET_PHY_PROFILE:
        return RadioSetPhyProfile.decode(payload)
    if msg_type is RadioType.STATUS_REPORT:
        return RadioStatusReport.decode(payload)
    _require_empty(payload, msg_type.name)
    return None


def decode_power(type: int, payload: bytes) -> object | None:
    msg_type = PowerType(type)
    if msg_type is PowerType.SET_OUTPUT:
        return PowerSetOutput.decode(payload)
    if msg_type is PowerType.SET_OUTPUT_MASK:
        return PowerSetOutputMask.decode(payload)
    if msg_type is PowerType.STATUS_REPORT:
        return PowerStatusReport.decode(payload)
    if msg_type is PowerType.BOARD_TELEMETRY:
        return PowerBoardTelemetry.decode(payload)
    _require_empty(payload, msg_type.name)
    return None


def decode_frame_payload(frame: protocol.Frame) -> object | bytes | None:
    """Decode known message families."""

    if frame.family == protocol.FAMILY_NETMGMT:
        return decode_netmgmt(frame.type, frame.payload)
    if frame.family == protocol.FAMILY_VIDEO:
        return decode_video(frame.type, frame.payload)
    if frame.family == protocol.FAMILY_FC_VIDEO:
        return decode_fc_video(frame.type, frame.payload)
    if frame.family == protocol.FAMILY_RADIO:
        return decode_radio(frame.type, frame.payload)
    if frame.family == protocol.FAMILY_POWER:
        return decode_power(frame.type, frame.payload)
    if frame.family == protocol.FAMILY_FC_COORD:
        return decode_fc_coord(frame.type, frame.payload)
    raise MessageError(f"unknown message family 0x{frame.family:02x}")


def _require_len(payload: bytes, expected: int, name: str) -> None:
    if len(payload) != expected:
        raise MessageError(f"{name} payload must be {expected} bytes")


def _require_empty(payload: bytes, name: str) -> None:
    if payload:
        raise MessageError(f"{name} payload must be empty")


def _u8(value: int, name: str) -> int:
    if not 0 <= value <= 0xFF:
        raise MessageError(f"{name} must fit in one byte")
    return value


def _i8(value: int, name: str) -> int:
    if not -128 <= value <= 127:
        raise MessageError(f"{name} must fit in signed one byte")
    return value


def _u16(value: int, name: str) -> int:
    if not 0 <= value <= 0xFFFF:
        raise MessageError(f"{name} must fit in two bytes")
    return value


def _u32(value: int, name: str) -> int:
    if not 0 <= value <= 0xFFFFFFFF:
        raise MessageError(f"{name} must fit in four bytes")
    return value
