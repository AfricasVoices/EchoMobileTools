import unittest

import pytz
from dateutil.parser import isoparse

from echo_mobile_session import EchoMobileSession, NoSessionDataError


class TestEchoMobileSession(unittest.TestCase):
    def test_echo_mobile_date_to_iso(self):
        session = EchoMobileSession()

        # Test providing a timezone explicitly or giving EAT
        self.assertEqual(
            session.echo_mobile_date_to_iso("2018-07-01 08:40", pytz.timezone("Africa/Nairobi")),
            "2018-07-01T08:40:00+03:00"
        )

        self.assertEqual(
            session.echo_mobile_date_to_iso("2018-07-01 08:40 EAT"),
            "2018-07-01T08:40:00+03:00"
        )

        # If a timezone is explicitly provided, always use this one.
        self.assertEqual(
            session.echo_mobile_date_to_iso("2018-07-01 08:40 EAT", pytz.timezone("UTC")),
            "2018-07-01T08:40:00+00:00"
        )

        # Providing any 3-letter timezone other than EAT should fail.
        self.assertRaises(
            ValueError,
            lambda: session.echo_mobile_date_to_iso("2018-07-01 08:40 UTC")
        )

        # Not providing a timezone when not logged-in should fail.
        self.assertRaises(
            NoSessionDataError,
            lambda: session.echo_mobile_date_to_iso("2018-07-01 08:40")
        )

        # Simulate effect of logging in which is relevant to the rest of this test case.
        session.login_data = {"tz": "Africa/Nairobi"}

        # Providing any 3-letter timezone other than EAT should still fail.
        self.assertRaises(
            ValueError,  # Because ends with an unknown timezone.
            lambda: session.echo_mobile_date_to_iso("2018-07-01 08:40 UTC"),
        )

        # Providing no timezone helper should cause the one set by logging in to be used.
        self.assertEqual(
            session.echo_mobile_date_to_iso("2018-07-01 08:40"),
            "2018-07-01T08:40:00+03:00"
        )

        # If a timezone is explicitly provided, always use this one.
        self.assertEqual(
            session.echo_mobile_date_to_iso("2018-07-01 08:40", pytz.timezone("UTC")),
            "2018-07-01T08:40:00+00:00"
        )

    def test_datetime_to_echo_mobile_datetime(self):
        session = EchoMobileSession()

        dt = isoparse("2018-07-02T19:40:00+03:00")

        # Should fail if not logged in.
        self.assertRaises(
            NoSessionDataError,
            lambda: session.datetime_to_echo_mobile_datetime(dt)
        )

        # Simulate effect of logging in which is relevant to the rest of this test case.
        session.login_data = {"tz": "Africa/Nairobi"}

        # Test normal data
        self.assertEqual(session.datetime_to_echo_mobile_datetime(dt).isoformat(), "2018-07-02T19:40:00+03:00")

        dt = isoparse("2018-07-02T19:40:00+01:00")
        self.assertEqual(session.datetime_to_echo_mobile_datetime(dt).isoformat(), "2018-07-02T21:40:00+03:00")

        dt = isoparse("2018-07-02T19:40:00Z")
        self.assertEqual(session.datetime_to_echo_mobile_datetime(dt).isoformat(), "2018-07-02T22:40:00+03:00")

    def test_normalise_message(self):
        input_message = {
            "date-time": "2018-06-02T10:33:00+03:00",
            "phone": "avf-phone-id-c4fd6565-a743-4b26-9432-3a80b1500194",
            "msg": "Hello!"
        }

        expected_repr = {
            "Date": 1527924780.0,
            "Sender": "avf-phone-id-c4fd6565-a743-4b26-9432-3a80b1500194",
            "Message": "Hello!"
        }

        self.assertDictEqual(
            expected_repr,
            EchoMobileSession.normalise_message(
                input_message, sender_key="phone", date_key="date-time", message_key="msg")
        )
