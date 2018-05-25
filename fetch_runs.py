import argparse
import time

import requests

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/cms/"

    parser = argparse.ArgumentParser(description="Poll EchoMobile for survey results")
    parser.add_argument("echo_mobile_username", metavar="echo-mobile-username", help="", nargs=1)
    parser.add_argument("echo_mobile_password", metavar="echo-mobile-password", help="User launching this program",
                        nargs=1)
    parser.add_argument("user", help="Identify of user launching this program", nargs=1)
    parser.add_argument("survey", help="Name of survey to download results of", nargs=1)

    args = parser.parse_args()
    echo_mobile_username = args.echo_mobile_username[0]
    echo_mobile_password = args.echo_mobile_password[0]
    target_survey_name = args.survey[0]

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
                                            params={"type": 13, "gen": "raw,label", "target": target_survey_id})
    rkey = report_generate_request.json()["rkey"]

    # Download the generated report, polling until it becomes available
    report_serve_response = "Unauthorized"
    while report_serve_response == "Unauthorized":  # Server returns unauthorized until the report is ready.
        report_serve_request = requests.get(BASE_URL + "report/serve", auth=auth, params={"rkey": rkey})
        report_serve_response = report_serve_request.text
        time.sleep(2)

    print("Downloaded CSV:")
    print(report_serve_response)

    # Delete the background task we made when generating the report
    cancel_request = requests.post(BASE_URL + "backgroundtask/cancel", auth=auth, params={"key": "report_" + rkey})
