import argparse
import os
import time
from io import StringIO

import six
from core_data_modules.traced_data import TracedData, Metadata
from core_data_modules.traced_data.io import TracedDataJsonIO
from core_data_modules.util import PhoneNumberUuidTable, IDUtils

from echo_mobile_session import EchoMobileSession

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
    parser.add_argument("survey_name", metavar="survey-name", help="Name of survey to download the results of", nargs=1)
    parser.add_argument("uuid_table", metavar="uuid-table", nargs=1,
                        help="JSON file containing an existing phone number <-> UUID lookup table. "
                             "This file will be updated with the new phone numbers which are found by this process.")
    parser.add_argument("output", help="JSON file to write serialized data to", nargs=1)

    args = parser.parse_args()
    verbose_mode = args.verbose
    user = args.user[0]
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    account_name = args.account[0]
    survey_name = args.survey_name[0]
    uuid_path = args.uuid_table[0]
    output_path = args.output[0]

    # Load the existing UUID table
    with open(uuid_path, "r") as f:
        uuid_table = PhoneNumberUuidTable.load(f)

    session = EchoMobileSession(verbose=verbose_mode)
    try:
        # Download survey report from Echo Mobile
        session.login(echo_mobile_username, echo_mobile_password)
        session.use_account_with_name(account_name)
        report = session.survey_report_for_name(survey_name)
    finally:
        session.delete_session_background_tasks()

    # Parse the downloaded report into a list of TracedData objects, de-identifying in the process.
    data = []
    for row in csv.DictReader(StringIO(report)):
        row["avf_phone_id"] = uuid_table.add_phone(row["phone"])
        row["avf_message_id"] = IDUtils.generate_uuid("avf-message-uuid-")
        del row["phone"]
        del row["name"]
        data.append(TracedData(dict(row), Metadata(user, Metadata.get_call_location(), time.time())))

    # Convert times to ISO
    for td in data:
        td.append_data(
            {
                "invited_date": session.echo_mobile_date_to_iso(td["invite_date"]),
                "start_date": session.echo_mobile_date_to_iso(td["start_date"]),
                "complete_date":
                    None if td["complete_date"] == "" else session.echo_mobile_date_to_iso(td["complete_date"])
            },
            Metadata(user, Metadata.get_call_location(), time.time())
        )

    # Write the UUIDs out to a file
    with open(uuid_path, "w") as f:
        uuid_table.dump(f)

    # Write the parsed items to a json file
    if os.path.dirname(output_path) is not "" and not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    with open(output_path, "w") as f:
        TracedDataJsonIO.export_traced_data_iterable_to_json(data, f, pretty_print=True)
