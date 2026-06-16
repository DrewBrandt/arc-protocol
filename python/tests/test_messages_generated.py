import unittest

from arc_protocol import messages
from arc_protocol import messages_generated as gen


class GeneratedMessageTests(unittest.TestCase):
    def test_netmgmt_ack_matches_public_messages(self):
        msg = gen.Ack(seq=0x1234)
        self.assertEqual(msg.encode(), messages.Ack(0x1234).encode())
        self.assertEqual(gen.Ack.decode(b"\x12\x34"), gen.Ack(0x1234))

    def test_radio_type_values_match_public_messages(self):
        for name in (
            "SET_FREQUENCY",
            "SET_TX_POWER",
            "GET_STATUS",
            "SET_PHY_PROFILE",
            "STATUS_REPORT",
        ):
            self.assertEqual(getattr(gen.RadioType, name), getattr(messages.RadioType, name))

    def test_fc_coord_payloads_match_public_messages(self):
        flight = gen.FlightTelemetry(
            time_ms=123456,
            stage=gen.FC_COORD_STAGE_BOOST,
            accel_x_mg=12,
            accel_y_mg=-34,
            accel_z_mg=987,
            vel_x_cms=100,
            vel_y_cms=-50,
            vel_z_cms=1234,
            lat_e7=391234567,
            lon_e7=-1049876543,
            alt_cm=123456,
            temp_cdeg=2345,
            voltage_mv=11900,
            gps_fix_quality=gen.FC_COORD_GPS_FIX_3D,
            roll_cdeg=120,
            pitch_cdeg=-450,
            yaw_cdeg=9012,
        )
        self.assertEqual(flight.encode(), messages.FlightTelemetry(**flight.__dict__).encode())
        self.assertEqual(gen.FlightTelemetry.decode(flight.encode()), flight)

        airbrake = gen.AirbrakeTelemetry(
            time_ms=2000,
            stage=gen.FC_COORD_STAGE_COAST,
            accel_x_mg=1,
            accel_y_mg=2,
            accel_z_mg=3,
            vel_x_cms=4,
            vel_y_cms=5,
            vel_z_cms=6,
            temp_cdeg=2500,
            voltage_mv=11800,
            roll_cdeg=10,
            pitch_cdeg=20,
            yaw_cdeg=30,
            airbrake_angle_cdeg=1250,
            predicted_apogee_cm=305000,
            original_apogee_estimate_cm=300000,
            blueraven_alt_cm=125000,
        )
        self.assertEqual(gen.AirbrakeTelemetry.decode(airbrake.encode()), airbrake)

        payload = gen.PayloadTelemetry(
            time_ms=3000,
            stage=gen.FC_COORD_STAGE_PAD,
            accel_x_mg=-1,
            accel_y_mg=-2,
            accel_z_mg=-3,
            vel_x_cms=0,
            vel_y_cms=0,
            vel_z_cms=0,
            temp_cdeg=2200,
            voltage_mv=12000,
            roll_cdeg=0,
            pitch_cdeg=0,
            yaw_cdeg=0,
            motor_x_um=123000,
            motor_y_um=-45000,
            percent_complete=42,
        )
        self.assertEqual(gen.PayloadTelemetry.decode(payload.encode()), payload)

    def test_radio_payloads_match_public_messages(self):
        cases = [
            (
                gen.RadioSetFrequency(433_920_000),
                messages.RadioSetFrequency(433_920_000),
            ),
            (
                gen.RadioSetTxPower(-10),
                messages.RadioSetTxPower(-10),
            ),
            (
                gen.RadioSetPhyProfile(gen.RADIO_PHY_PROFILE_FAST_BW500),
                messages.RadioSetPhyProfile(messages.RADIO_PHY_PROFILE_FAST_BW500),
            ),
            (
                gen.RadioStatusReport(
                    frequency_hz=433_920_000,
                    tx_power_dbm=17,
                    rssi_dbm=-78,
                    snr_db=9,
                    error_flags=gen.RADIO_ERR_RX_OVERRUN,
                    packets_rx=1024,
                    packets_tx=256,
                ),
                messages.RadioStatusReport(
                    frequency_hz=433_920_000,
                    tx_power_dbm=17,
                    rssi_dbm=-78,
                    snr_db=9,
                    error_flags=messages.RADIO_ERR_RX_OVERRUN,
                    packets_rx=1024,
                    packets_tx=256,
                ),
            ),
        ]
        for generated, public in cases:
            with self.subTest(generated=generated):
                self.assertEqual(generated.encode(), public.encode())
                self.assertEqual(type(generated).decode(public.encode()), generated)

    def test_generated_decoders_match_public_messages(self):
        payload = messages.RadioSetFrequency(915_500_000).encode()
        self.assertEqual(
            gen.decode_radio(gen.RadioType.SET_FREQUENCY, payload),
            gen.RadioSetFrequency(915_500_000),
        )
        self.assertEqual(gen.decode_radio(gen.RadioType.GET_STATUS, b""), None)
        self.assertEqual(
            gen.decode_radio(
                gen.RadioType.SET_PHY_PROFILE,
                bytes((gen.RADIO_PHY_PROFILE_FAST_BW500,)),
            ),
            gen.RadioSetPhyProfile(gen.RADIO_PHY_PROFILE_FAST_BW500),
        )
        self.assertEqual(
            gen.decode_fc_coord(gen.FcCoordType.FLIGHT_TELEMETRY, gen.FlightTelemetry(
                time_ms=1,
                stage=gen.FC_COORD_STAGE_PAD,
                accel_x_mg=0,
                accel_y_mg=0,
                accel_z_mg=1000,
                vel_x_cms=0,
                vel_y_cms=0,
                vel_z_cms=0,
                lat_e7=0,
                lon_e7=0,
                alt_cm=0,
                temp_cdeg=2000,
                voltage_mv=12000,
                gps_fix_quality=gen.FC_COORD_GPS_FIX_NONE,
                roll_cdeg=0,
                pitch_cdeg=0,
                yaw_cdeg=0,
            ).encode()).stage,
            gen.FC_COORD_STAGE_PAD,
        )

        with self.assertRaises(gen.MessageError):
            gen.decode_radio(gen.RadioType.GET_STATUS, b"bad")


if __name__ == "__main__":
    unittest.main()
