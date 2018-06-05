import argparse
import os
import time
from io import StringIO

import requests
from core_data_modules.traced_data.io import TracedDataCSVIO, TracedDataJsonIO

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/cms/"

    parser = argparse.ArgumentParser(description="Poll Echo Mobile for survey results")
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="Echo Mobile username", nargs=1)
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="Echo Mobile password", nargs=1)
    parser.add_argument("user", help="Identifier of user launching this program", nargs=1)
    parser.add_argument("survey_name", metavar="survey-name", help="Name of survey to download the results of", nargs=1)
    parser.add_argument("output", help="JSON file to write serialized data to", nargs=1)

    args = parser.parse_args()
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    user = args.user[0]
    target_survey_name = args.survey_name[0]
    output_path = args.output[0]

    auth = (echo_mobile_username, echo_mobile_password)

    # Determine ID of survey
    target_request = requests.get(BASE_URL + "survey", auth=auth)
    target_response = target_request.json()
    matching_surveys = [survey for survey in target_response["surveys"] if survey["name"] == target_survey_name]

    if len(matching_surveys) == 0:
        print("Error: Requested survey not found on Echo Mobile.")
        exit(1)

    if len(matching_surveys) > 1:
        # Not sure if this can actually happen but being defensive just in case.
        print("Error: Survey name is ambiguous. The requested survey name matched the following surveys:")
        for survey in matching_surveys:
            print("  key: " + survey["key"])
            print("    Number of questions: " + str(survey["n_questions"]))
            print("    Invitation message: " + survey["invite_message"])
            print("    Thanks message: " + survey["thanks_message"])
        print("Please report this incident to the project developers.")
        exit(1)

    target_survey_id = matching_surveys[0]["key"]

    # Generate a report for that survey
    report_generate_request = requests.post(BASE_URL + "report/generate", auth=auth,
                                            # Type is undocumented, but from inspection of the calls the website is
                                            # making it turns out that '13' is the magic number we need here.
                                            params={"type": 13, "gen": "raw,label",
                                                    "std_field": "name,phone", "target": target_survey_id})
    rkey = report_generate_request.json()["rkey"]

    try:
        # Poll for report status until the report has stopped generating.
        # Status is not documented, but from observation '1' means generating and '3' means successfully generated
        report_status = 1
        while report_status == 1:
            report_status_request = requests.get(BASE_URL + "backgroundtask", auth=auth)
            report_status = report_status_request.json()["tasks"]["report_" + rkey]["status"]
            time.sleep(2)
        assert report_status == 3, "Report stopped generating, but with an unknown status"

        # Download the generated report
        report_serve_request = requests.get(BASE_URL + "report/serve", auth=auth, params={"rkey": rkey})
        report_serve_response = report_serve_request.text

        # Parse the downloaded report into a list of TracedData objects
        data = list(TracedDataCSVIO.import_csv_to_traced_data_iterable(user, StringIO(report_serve_response)))

        # Write the parsed items to a json file
        if os.path.dirname(output_path) is not "" and not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, "w") as f:
            TracedDataJsonIO.export_traced_data_iterable_to_json(data, f, pretty_print=True)
    finally:
        # Delete the background task we made when generating the report
        cancel_request = requests.post(BASE_URL + "backgroundtask/cancel", auth=auth, params={"key": "report_" + rkey})
