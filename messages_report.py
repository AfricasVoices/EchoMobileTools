import argparse
import os
import time
from io import StringIO

import six
from core_data_modules.traced_data import TracedData, Metadata
from core_data_modules.traced_data.io import TracedDataJsonIO
from core_data_modules.util import PhoneNumberUuidTable, MessageUuidTable
from dateutil.parser import isoparse

from echo_mobile_session import EchoMobileSession, MessageDirection

if six.PY2:
    import unicodecsv as csv
if six.PY3:
    import csv

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/"

    parser = argparse.ArgumentParser(description="Poll Echo Mobile for survey results")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("user", help="Identifier of user launching this program", nargs=1)
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="Echo Mobile username", nargs=1)
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="Echo Mobile password", nargs=1)
    parser.add_argument("account", help="Name of Echo Mobile organisation to log into", nargs=1)
    parser.add_argument("start_date", metavar="start-date", help="Inclusive start date of message range to export, "
                                                                 "in ISO format", nargs=1)
    parser.add_argument("end_date", metavar="end-date", help="Exclusive end date of message range to export, "
                                                             "in ISO format", nargs=1)
    parser.add_argument("phone_uuid_table", metavar="phone-uuid-table", nargs=1,
                        help="JSON file containing an existing phone number <-> UUID lookup table. "
                             "This file will be updated with the new phone numbers which are found by this process.")
    parser.add_argument("message_uuid_table", metavar="message-uuid-table", nargs=1,
                        help="JSON file containing an existing message -> UUID lookup table. "
                             "This file will be updated with the new messages which are found by this process.")
    parser.add_argument("json_output", metavar="json-output", help="JSON file to write serialized data to", nargs=1)

    args = parser.parse_args()
    verbose_mode = args.verbose
    user = args.user[0]
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    account_name = args.account[0]
    start_date_iso = args.start_date[0]
    end_date_iso = args.end_date[0]
    phone_uuid_path = args.phone_uuid_table[0]
    message_uuid_path = args.message_uuid_table[0]
    json_output_path = args.json_output[0]

    # Parse the provided ISO dates
    user_start_date = isoparse(start_date_iso)
    user_end_date = isoparse(end_date_iso)

    # TODO: Test that isoparse is only accepting dates with time-zone offsets.
    # TODO: Print a helpful message if the user enters an invalid ISO date.

    # Load the existing UUID tables
    with open(phone_uuid_path, "r") as f:
        phone_uuids = PhoneNumberUuidTable.load(f)
    with open(message_uuid_path, "r") as f:
        message_uuids = MessageUuidTable.load(f)

    session = EchoMobileSession(verbose=verbose_mode)
    try:
        # Download inbox report from Echo Mobile.
        session.login(echo_mobile_username, echo_mobile_password)
        session.use_account_with_name(account_name)

        # Convert start/end dates into an Echo Mobile time zone.
        echo_mobile_start_date = session.date_to_echo_mobile_timezone(user_start_date)
        echo_mobile_end_date = session.date_to_echo_mobile_timezone(user_end_date)

        report = session.messages_report(
            echo_mobile_start_date.strftime("%Y-%m-%d"), echo_mobile_end_date.strftime("%Y-%m-%d"),
            direction=MessageDirection.Incoming)
    finally:
        # Delete the background task we made when generating the report
        session.delete_session_background_tasks()

    # Parse the downloaded report into a list of TracedData objects, de-identifying in the process.
    messages = []
    for row in csv.DictReader(StringIO(report)):
        row["avf_phone_id"] = phone_uuids.add_phone(row["Phone"])
        del row["Phone"]
        messages.append(TracedData(dict(row), Metadata(user, Metadata.get_call_location(), time.time())))

    # Convert times to ISO
    for td in messages:
        td.append_data(
            {"Date": session.echo_mobile_date_to_iso(td["Date"])},
            Metadata(user, Metadata.get_call_location(), time.time())
        )

    # Filter out messages sent outwith the desired time range.
    messages = list(filter(lambda td: echo_mobile_start_date <= isoparse(td["Date"]) < echo_mobile_end_date, messages))

    # Add a unique id to each message
    for td in messages:
        td.append_data(
            {"avf_message_id": message_uuids.add_message(
                EchoMobileSession.normalise_message(td, "avf_phone_id", "Date", "Message"))},
            Metadata(user, Metadata.get_call_location(), time.time())
        )

    # Write the UUIDs out to a file
    with open(phone_uuid_path, "w") as f:
        phone_uuids.dump(f)
    with open(message_uuid_path, "w") as f:
        message_uuids.dump(f)

    # Write the parsed messages to a json file
    if os.path.dirname(json_output_path) is not "" and not os.path.exists(os.path.dirname(json_output_path)):
        os.makedirs(os.path.dirname(json_output_path))
    with open(json_output_path, "w") as f:
        TracedDataJsonIO.export_traced_data_iterable_to_json(messages, f, pretty_print=True)
