import argparse
from os import path

from echo_mobile_session import EchoMobileSession

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/"

    parser = argparse.ArgumentParser(description="Poll Echo Mobile for survey results")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("user", help="Identifier of user launching this program", nargs=1)
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="Echo Mobile username", nargs=1)
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="Echo Mobile password", nargs=1)
    parser.add_argument("account", help="Name of Echo Mobile organisation to log into", nargs=1)
    parser.add_argument("output", help="Directory to write serialized data to", nargs=1)

    args = parser.parse_args()
    verbose_mode = args.verbose
    user = args.user[0]
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    account_name = args.account[0]
    output_path = args.output[0]

    session = EchoMobileSession(verbose=verbose_mode)
    try:
        # Download survey report from Echo Mobile
        session.login(echo_mobile_username, echo_mobile_password)
        session.use_account_with_name(account_name)

        for survey in session.surveys():
            report = session.survey_report_for_key(survey["key"])

            with open(path.join(output_path, "{}.csv".format(survey["name"])), "w") as f:
                f.write(report)
    finally:
        session.delete_session_background_tasks()
