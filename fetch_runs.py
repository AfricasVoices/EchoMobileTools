import time

import requests

if __name__ == "__main__":
    BASE_URL = "https://www.echomobile.org/api/cms/"

    USER = ""
    PASSWORD = ""
    SURVEY = ""

    AUTH = (USER, PASSWORD)

    # Determine ID of survey
    target_request = requests.get(BASE_URL + "survey", auth=AUTH)
    target_response = target_request.json()
    matching_surveys = [survey for survey in target_response["surveys"] if survey["name"] == SURVEY]

    if len(matching_surveys) == 0:
        print("Error: Survey not found")
        exit(1)

    if len(matching_surveys) > 1:
        print("Error: Survey name ambiguous")  # Not sure if this can actually happen but being defensive just in case.
        exit(1)

    target = matching_surveys[0]["key"]

    # Generate a report for that survey
    generate_request = requests.post(BASE_URL + "report/generate", auth=AUTH,
                                     params={"type": 13, "gen": "raw,label", "std_field": "", "target": target})
    rkey = generate_request.json()["rkey"]

    # Download the generated report, polling while it is unavailable
    serve_response = "Unauthorized"
    while serve_response == "Unauthorized":  # Server returns unauthorized until the report is ready.
        serve_request = requests.get(BASE_URL + "serve", auth=AUTH, params={"rkey": rkey})
        serve_response = serve_request.text
        time.sleep(2)

    print("Downloaded CSV:")
    print(serve_response)

    # Delete the background task we made when generating the report
    cancel_request = requests.post(BASE_URL + "backgroundtask/cancel", auth=AUTH, params={"key": "report_" + rkey})
