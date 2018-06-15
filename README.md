# Echo Mobile Experiments
Contains tools for downloading survey and inbox reports from Echo Mobile, and exporting these reports to formats
suitable for processing by later stages of the pipeline.

Contains a tool which downloads the results of an Echo Mobile survey, converts these to `TracedData` objects, and 
exports to a JSON file ready for consumption by the rest of the pipeline.

## Set-Up
1. Install Pipenv: `$ pip install pipenv`.

1. Install dependencies: `$ pipenv sync`.

## Usage
### Survey Report
To generate and download a survey report, and export to a TracedData JSON file:
```
$ pipenv run python survey_report.py <user> <echo-mobile-username> <echo-mobile-password> <account> <survey-name> <output>
```
where:
- `user` is the identifier of the user launching the program,
- `echo-mobile-username` is the email address of the user to log in to Echo Mobile as,
- `echo-mobile-password` is the password to use when logging into Echo Mobile,
- `account` is the name of the Echo Mobile organisation to log into,
- `survey-name` is the name of the survey to download e.g. `Socio-demographic survey 1`, and
- `output` is the path to a JSON file where the report output should be written to.
    
### Inbox Report
To generate and download a global inbox report, and export to a TracedData JSON file:
```
$ pipenv run python inbox_report.py <user> <echo-mobile-username> <echo-mobile-password> <account> <uuid-table-output> <json-output>
```
where:
- `user` is the identifier of the user launching the program,
- `echo-mobile-username` is the email address of the user to log in to Echo Mobile as,
- `echo-mobile-password` is the password to use when logging into Echo Mobile,
- `account` is the name of the Echo Mobile organisation to log into,
- `uuid-table-output` is the the path to a JSON file to write the phone number <-> UUID table to, and
- `output` is the path to a JSON file where the report output should be written to.

To generate and download a report for the inbox of a specific group, add the flag `--inbox <group-name>`.
   
This project is configured to use Python 3.6 by default, but all code is Python 2.7 compliant.

### Configuring Parameters
To change which contact and response fields are downloaded (e.g. "raw, labelled"),
set the `response_formats` and `contact_fields` parameters of the calls
to `session.survey_report_for_name` or `session.inbox_report`.
Refer to the documentation for those functions for the full
list of options.
