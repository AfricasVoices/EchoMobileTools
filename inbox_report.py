import argparse
import os
import time
from io import StringIO

import six
from core_data_modules.traced_data import TracedData, Metadata
from core_data_modules.traced_data.io import TracedDataJsonIO
from core_data_modules.util import PhoneNumberUuidTable, MessageUuidTable

from echo_mobile_session import EchoMobileSession

if six.PY2:
    import unicodecsv as csv
if six.PY3:
    import csv

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/"

    parser = argparse.ArgumentParser(description="Poll Echo Mobile for survey results")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("user", help="Identifier of user launching this program, for use by TracedData Metadata")
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="Echo Mobile username")
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="Echo Mobile password")
    parser.add_argument("account", help="Name of Echo Mobile organisation to log into")
    parser.add_argument("--inbox", help="Only download messages from the specified inbox name."
                                        "If this flag is omitted, messages from all inboxes will be exported")
    parser.add_argument("phone_uuid_table_path", metavar="phone-uuid-table-path",
                        help="JSON file containing an existing phone number <-> UUID lookup table. "
                             "This file will be updated with the new phone numbers which are found by this process.")
    parser.add_argument("message_uuid_table_path", metavar="message-uuid-table-path",
                        help="JSON file containing an existing message -> UUID lookup table. "
                             "This file will be updated with the new messages which are found by this process.")
    parser.add_argument("json_output_path", metavar="json-output-path",
                        help="Path to a JSON file to write processed TracedData messages to")

    args = parser.parse_args()
    verbose_mode = args.verbose
    user = args.user
    echo_mobile_username = args.echo_mobile_username
    echo_mobile_password = args.echo_mobile_password
    account_name = args.account
    inbox = args.inbox
    phone_uuid_path = args.phone_uuid_table_path
    message_uuid_path = args.message_uuid_table_path
    json_output_path = args.json_output_path

    # Load the existing UUID table
    with open(phone_uuid_path, "r") as f:
        phone_uuids = PhoneNumberUuidTable.load(f)
    with open(message_uuid_path, "r") as f:
        message_uuids = MessageUuidTable.load(f)

    session = EchoMobileSession(verbose=verbose_mode)
    try:
        # Download inbox report from Echo Mobile.
        session.login(echo_mobile_username, echo_mobile_password)
        session.use_account_with_name(account_name)
        report = session.inbox_report(inbox)
    finally:
        # Delete the background task we made when generating the report
        session.delete_session_background_tasks()

    # Parse the downloaded report into a list of TracedData objects, de-identifying in the process.
    messages = []
    for row in csv.DictReader(StringIO(report)):
        row["avf_phone_id"] = phone_uuids.add_phone(row["Phone"])
        del row["Phone"]
        del row["Sender"]
        messages.append(TracedData(dict(row), Metadata(user, Metadata.get_call_location(), time.time())))

    # Convert times to ISO
    for td in messages:
        td.append_data(
            {
                "Date": session.echo_mobile_date_to_iso(td["Date"]),
                "upload_date": session.echo_mobile_date_to_iso(td["upload_date"]),
            },
            Metadata(user, Metadata.get_call_location(), time.time())
        )

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
