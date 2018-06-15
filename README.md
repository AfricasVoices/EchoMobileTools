# Echo Mobile Experiments
Contains a tool which downloads the results of an Echo Mobile survey, converts these to `TracedData` objects, and 
exports to a JSON file ready for consumption by the rest of the pipeline.

## Usage
1. Install Pipenv: `$ pip install pipenv`.

1. Install dependencies: `$ pipenv sync`.

1. Run:
   ```
   $ pipenv run python fetch_report.py <echo-mobile-username> <echo-mobile-password> <user> <survey-name> <output>
   ```
   where:
    - `echo-mobile-username` is the email address of the user to log in to Echo Mobile as,
    - `echo-mobile-password` is the password to use when logging into Echo Mobile,
    - `user` is the identifier of the user launching the program,
    - `survey-name` is the name of the survey to download e.g. `Socio-demographic survey 1`, and
    - `output` is the path to a JSON file where the output should be written to.
   
This project is configured to use Python 3.6 by default, but all code is Python 2.7 compliant.

### Configuring Parameters
By default, the raw and labelled responses are downloaded, along with the name and phone number fields.

To change this, set the `response_formats` and `contact_fields` parameters of the call 
to `session.report_for_survey_name` in `fetch_report.py`. Refer to the documentation for that function for the full
list of options.
