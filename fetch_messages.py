import argparse
import os
import time
from io import StringIO

from core_data_modules.traced_data import TracedData, Metadata
from core_data_modules.traced_data.io import TracedDataCSVIO, TracedDataJsonIO
from core_data_modules.util import PhoneNumberUuidTable, IDUtils

from echo_mobile_session import EchoMobileSession

import six

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
    parser.add_argument("--inbox", help="Only download messages from the specified inbox", type=str)
    parser.add_argument("uuid_output", metavar="uuid-table-output",
                        help="JSON file to write phone number/UUID lookup table to")
    parser.add_argument("json_output", metavar="json-output", help="JSON file to write serialized data to", nargs=1)

    args = parser.parse_args()
    verbose_mode = args.verbose
    user = args.user[0]
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    account_name = args.account[0]
    inbox = args.inbox
    uuid_table_output_path = args.uuid_output[0]
    json_output_path = args.json_output[0]

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
    uuid_table = PhoneNumberUuidTable()
    for row in csv.DictReader(StringIO(report)):
        row["avf_phone_id"] = uuid_table.add_phone(row["Phone"])
        row["avf_message_id"] = IDUtils.generate_uuid("av-message-uuid-")
        del row["Phone"]
        del row["Sender"]
        messages.append(TracedData(dict(row), Metadata(user, Metadata.get_call_location(), time.time())))

    # Write the UUIDs out to a file
    if os.path.dirname(uuid_table_output_path) is not "" and not os.path.exists(os.path.dirname(uuid_table_output_path)):
        os.makedirs(os.path.dirname(uuid_table_output_path))
    with open(uuid_table_output_path, "w") as f:
        uuid_table.dump(f)

    # Write the parsed messages to a json file
    if os.path.dirname(json_output_path) is not "" and not os.path.exists(os.path.dirname(json_output_path)):
        os.makedirs(os.path.dirname(json_output_path))
    with open(json_output_path, "w") as f:
        TracedDataJsonIO.export_traced_data_iterable_to_json(messages, f, pretty_print=True)
