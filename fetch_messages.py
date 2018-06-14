import argparse
import os
from io import StringIO

from core_data_modules.traced_data.io import TracedDataCSVIO, TracedDataJsonIO

from echo_mobile_session import EchoMobileSession

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/"

    parser = argparse.ArgumentParser(description="Poll Echo Mobile for survey results")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("user", help="Identifier of user launching this program", nargs=1)
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="Echo Mobile username", nargs=1)
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="Echo Mobile password", nargs=1)
    parser.add_argument("account", help="Name of Echo Mobile organisation to log into", nargs=1)
    parser.add_argument("output", help="JSON file to write serialized data to", nargs=1)

    args = parser.parse_args()
    verbose_mode = args.verbose
    user = args.user[0]
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    account_name = args.account[0]
    output_path = args.output[0]

    session = EchoMobileSession(verbose=verbose_mode)
    try:
        session.login(echo_mobile_username, echo_mobile_password)
        session.use_account_with_name(account_name)
        report = session.global_inbox_report()

        # Parse the downloaded report into a list of TracedData objects
        data = list(TracedDataCSVIO.import_csv_to_traced_data_iterable(user, StringIO(report)))

        # Write the parsed items to a json file
        if os.path.dirname(output_path) is not "" and not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, "w") as f:
            TracedDataJsonIO.export_traced_data_iterable_to_json(data, f, pretty_print=True)

        # Write the parsed items to a csv file
        # TODO: Accept path as a commond line argument.
        output_path_csv = "output.csv"
        if os.path.dirname(output_path_csv) is not "" and not os.path.exists(os.path.dirname(output_path_csv)):
            os.makedirs(os.path.dirname(output_path_csv))
        with open(output_path_csv, "w") as f:
            TracedDataCSVIO.export_traced_data_iterable_to_csv(data, f)
    finally:
        # Delete the background task we made when generating the report
        session.delete_session_background_tasks()
