import argparse
import json
import os
import time
from io import BytesIO

import jsonpickle
import requests
from core_data_modules.traced_data.io import TracedDataCSVIO

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/cms/"

    parser = argparse.ArgumentParser(description="Poll EchoMobile for survey results")
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="Echo Mobile username", nargs=1)
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="Echo Mobile password", nargs=1)
    parser.add_argument("user", help="Identifier of user launching this program", nargs=1)
    parser.add_argument("survey_name", metavar="survey-name", help="Name of survey to download results of", nargs=1)
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
        print("Error: Survey not found")
        exit(1)

    if len(matching_surveys) > 1:
        print("Error: Survey name ambiguous")  # Not sure if this can actually happen but being defensive just in case.
        exit(1)

    target_survey_id = matching_surveys[0]["key"]

    # Generate a report for that survey
    report_generate_request = requests.post(BASE_URL + "report/generate", auth=auth,
                                            params={"type": 13, "gen": "raw", "target": target_survey_id})
    rkey = report_generate_request.json()["rkey"]

    # Download the generated report, polling until it becomes available
    report_serve_response = "Unauthorized"
    while report_serve_response == "Unauthorized":  # Server returns unauthorized until the report is ready.
        report_serve_request = requests.get(BASE_URL + "report/serve", auth=auth, params={"rkey": rkey})
        report_serve_response = report_serve_request.text
        time.sleep(2)

    # Parse the downloaded report into a list of TracedData objects
    data = list(TracedDataCSVIO.import_csv_to_traced_data_iterable(user, BytesIO(report_serve_response.encode())))

    # Write the parsed items to a json file
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    with open(output_path, "wb") as f:
        # Serialize the list of TracedData to a format which can be trivially deserialized.
        pickled = jsonpickle.dumps(data)

        # Pretty-print the serialized json
        pp = json.dumps(json.loads(pickled), indent=2, sort_keys=True).encode()

        # Write pretty-printed JSON to a file.
        f.write(pp)

    # Delete the background task we made when generating the report
    cancel_request = requests.post(BASE_URL + "backgroundtask/cancel", auth=auth, params={"key": "report_" + rkey})
