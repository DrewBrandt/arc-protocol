# ARC Message Codegen

The message schema lives at:

```text
schema/messages.json
```

Generate checked-in helpers with:

```bash
python tools/generate_messages.py
```

Check that generated files match the schema:

```bash
python tools/generate_messages.py --check
# or
make check-codegen
```

Current generated scope is fixed-size scalar messages:

- `NETMGMT`
- `FC_COORD` telemetry (`FLIGHT_TELEMETRY`, `AIRBRAKE_TELEMETRY`,
  `PAYLOAD_TELEMETRY`)
- `RADIO`

`POWER` still has hand-written helpers because its existing `STATUS_REPORT` is
variable-length. Its fixed-size `BOARD_TELEMETRY` helper lives beside that
hand-written code for now.

Generated C files are firmware-facing:

```text
src/arc_messages_netmgmt.h
src/arc_messages_netmgmt.c
src/arc_messages_fc_coord.h
src/arc_messages_fc_coord.c
src/arc_messages_radio.h
src/arc_messages_radio.c
```

Generated Python lives beside the public hand-written module for now:

```text
python/arc_protocol/messages_generated.py
```

The existing public `messages.py` remains in place while codegen is young.
Tests compare the generated module against the public API so we can migrate
once enough families are covered.

## Firmware Implementation Pattern

Firmware should treat ARC message helpers as payload codecs, not transport
logic. The transport still does COBS/UART, LoRa, BLE, retries, and routing.

Typical receive flow:

```c
arc_frame_t f;
if (arc_frame_parse(raw, raw_len, &f) != ARC_OK) {
    return;
}

if (f.dst != MY_ADDR && f.dst != ARC_ADDR_BROADCAST) {
    forward_frame(&f);
    return;
}

if (f.family == ARC_FAMILY_RADIO && f.type == ARC_RADIO_SET_FREQUENCY) {
    arc_radio_set_frequency_t msg;
    if (arc_radio_set_frequency_decode(f.payload, f.payload_len, &msg) != ARC_OK) {
        return;
    }

    if (f.flags & ARC_FLAG_RELIABLE) {
        send_ack(&f);
    }

    schedule_frequency_hop(msg.frequency_hz);
}

if (f.family == ARC_FAMILY_RADIO && f.type == ARC_RADIO_SET_PHY_PROFILE) {
    arc_radio_set_phy_profile_t msg;
    if (arc_radio_set_phy_profile_decode(f.payload, f.payload_len, &msg) != ARC_OK) {
        return;
    }

    if (f.flags & ARC_FLAG_RELIABLE) {
        send_ack(&f);
    }

    schedule_phy_profile_switch(msg.profile_id);
}
```

Common message families should be implemented by every node that advertises
that family:

- `NETMGMT`: common node management and liveness.
- `FC_COORD`: flight computer, airbrake, and payload telemetry/coordination.
- `RADIO`: only radio-class nodes.
- `POWER`: only power controllers.
- `VIDEO` / `FC_VIDEO`: video control nodes.

A node that receives an unsupported family/type addressed to itself should
drop it for now. Later, add an explicit `NETMGMT` error/status response once
we need operator-visible negative ACKs.

## Design Rules

- Heartbeat is empty. It says "node `src` is alive"; status belongs in status
  messages.
- Reliable commands are ACKed at ARC transport level, then acted on. For
  frequency changes, ACK on the old frequency before hopping.
- Prefer named profile commands for dangerous multi-parameter radio changes
  such as bandwidth/spreading-factor sets. `RADIO SET_PHY_PROFILE` currently
  defines `ARC_RADIO_PHY_PROFILE_SAFE_BW125` and
  `ARC_RADIO_PHY_PROFILE_FAST_BW500`.
- Do not overload `SESSION_RESET` as a device reboot. Protocol/session reset,
  MCU reboot, radio-chip reset, and pipeline restart are different operations.
- Telemetry uses scaled integers in field names: `lat_e7`, `alt_cm`,
  `temp_cdeg`, `roll_cdeg`, `motor_x_um`, etc. Do not send floats on the wire.
