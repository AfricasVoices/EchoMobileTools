import argparse
import os
import time
from io import StringIO

import requests
from core_data_modules.traced_data.io import TracedDataCSVIO, TracedDataJsonIO

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/"

    parser = argparse.ArgumentParser(description="Poll Echo Mobile for survey results")
    parser.add_argument("user", help="Identifier of user launching this program", nargs=1)
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="Echo Mobile username", nargs=1)
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="Echo Mobile password", nargs=1)
    parser.add_argument("account", help="Name of Echo Mobile organisation to log into", nargs=1)
    parser.add_argument("survey_name", metavar="survey-name", help="Name of survey to download the results of", nargs=1)
    parser.add_argument("output", help="JSON file to write serialized data to", nargs=1)

    args = parser.parse_args()
    user = args.user[0]
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    account_name = args.account[0]
    target_survey_name = args.survey_name[0]
    output_path = args.output[0]

    session = requests.Session()

    # Log in to Echo Mobile
    login_request = session.post(BASE_URL + "authenticate/simple",
                                 params={"_login": echo_mobile_username, "_pw": echo_mobile_password,
                                         # auth is a magic API key extracted from echomobile.org/dist/src/app.build.js
                                         "auth": "JXEIUOVNQLKJDDHA2J", "populate_session": 1})

    # Determine key of desired account
    account_request = session.get(BASE_URL + "cms/account/me", params={"with_linked": 1})
    accounts = account_request.json()
    matching_accounts = [account for account in accounts["linked"] if account["ent_name"] == account_name]

    if len(matching_accounts) == 0:
        print("Error: Requested account not found. The available accounts for this user are:")
        for account in accounts["linked"]:
            print(account["ent_name"])
        exit(1)

    account_key = matching_accounts[0]["key"]

    # Switch to the desired account
    linked_request = session.post(BASE_URL + "authenticate/linked",
                                  params={"acckey": account_key})

    # Download the global inbox.
    # Generate a report for that survey
    report_generate_request = session.post(BASE_URL + "cms/report/generate",
                                           params={"type": 11, "ftype": 1,
                                                   "std_field": "internal_id,group,referrer,upload_date,"
                                                                "last_survey_complete_date,"
                                                                "geo,locationTextRaw,labels"})
    rkey = report_generate_request.json()["rkey"]

    try:
        # Poll for report status until the report has stopped generating.
        # Status is not documented, but from observation '1' means generating and '3' means successfully generated
        report_status = 1
        while report_status == 1:
            report_status_request = session.get(BASE_URL + "cms/backgroundtask")
            report_status = report_status_request.json()["tasks"]["report_" + rkey]["status"]
            time.sleep(2)
        assert report_status == 3, "Report stopped generating, but with an unknown status"

        # Download the generated report
        report_serve_request = session.get(BASE_URL + "cms/report/serve", params={"rkey": rkey})
        report_serve_response = report_serve_request.text

        # Parse the downloaded report into a list of TracedData objects
        data = list(TracedDataCSVIO.import_csv_to_traced_data_iterable(user, StringIO(report_serve_response)))

        # Write the parsed items to a json file
        if os.path.dirname(output_path) is not "" and not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, "w") as f:
            TracedDataJsonIO.export_traced_data_iterable_to_json(data, f, pretty_print=True)

        # Write the parsed items to a json file
        output_path_csv = "output.csv"
        if os.path.dirname(output_path_csv) is not "" and not os.path.exists(os.path.dirname(output_path_csv)):
            os.makedirs(os.path.dirname(output_path_csv))
        with open(output_path_csv, "w") as f:
            TracedDataCSVIO.export_traced_data_iterable_to_csv(data, f)
    finally:
        # Delete the background task we made when generating the report
        cancel_request = session.post(BASE_URL + "cms/backgroundtask/cancel", params={"key": "report_" + rkey})
