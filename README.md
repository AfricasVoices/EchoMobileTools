# Echo Mobile Experiments
Contains tools for downloading survey and inbox reports from Echo Mobile, and exporting these reports to formats
suitable for processing by later stages of the pipeline.

Contains a tool which downloads the results of an Echo Mobile survey, converts these to `TracedData` objects, and 
exports to a JSON file ready for consumption by the rest of the pipeline.

## Set-Up
1. Install Pipenv: `$ pip install pipenv`.

1. Install dependencies: `$ pipenv --three && pipenv sync`.

## Usage
### Survey Report
To generate and download a survey report, and export to a TracedData JSON file:
```
$ pipenv run python survey_report.py <user> <echo-mobile-username> <echo-mobile-password> <account> <survey-name> <phone-uuid-table-path> <output>
```
where:
- `user` is the identifier of the user launching the program,
- `echo-mobile-username` is the email address of the user to log in to Echo Mobile as,
- `echo-mobile-password` is the password to use when logging into Echo Mobile,
- `account` is the name of the Echo Mobile organisation to log into,
- `survey-name` is the name of the survey to download e.g. `"Socio-demographic survey 1"`,
- `phone-uuid-table-path` is the the path to a JSON file containing an existing phone number <-> UUID table to use and update, and
- `output` is the path to a JSON file where the report output should be written to.

### Messages Report
To generate and download all incoming messages received in a given time range (including survey responses), 
and export to a TracedData file:
```
$ pipenv run python mesages_report.py <user> <echo-mobile-username> <echo-mobile-password> <account> <start-date> <end-date> <phone-uuid-table-path> <message-uuid-table-path> <json-output>
```
where:
- `user` is the identifier of the user launching the program,
- `echo-mobile-username` is the email address of the user to log in to Echo Mobile as,
- `echo-mobile-password` is the password to use when logging into Echo Mobile,
- `account` is the name of the Echo Mobile organisation to log into,
- `start-date` is the inclusive start range of messages to export, expressed as an ISO time string e.g `2018-06-15T17:19:42+03:00`,
- `end` is the exclusive end range of messages to export, expressed as an ISO time string,
- `phone-uuid-table-path` is the the path to a JSON file containing an existing phone number <-> UUID table to use and update,
- `message-uuid-table-path` is the the path to a JSON file containing an existing message -> UUID table to use and update, and
- `output` is the path to a JSON file where the report output should be written to.
    
### Inbox Report
To generate and download a global inbox report (all incoming messages which are not survey answers),
and export to a TracedData JSON file:
```
$ pipenv run python inbox_report.py <user> <echo-mobile-username> <echo-mobile-password> <account> <phone-uuid-table-path> <message-uuid-table-path> <json-output>
```
where:
- `user` is the identifier of the user launching the program,
- `echo-mobile-username` is the email address of the user to log in to Echo Mobile as,
- `echo-mobile-password` is the password to use when logging into Echo Mobile,
- `account` is the name of the Echo Mobile organisation to log into,
- `phone-uuid-table` is the the path to a JSON file containing an existing phone number <-> UUID table to use and update,
- `message-uuid-table` is the the path to a JSON file containing an existing message -> UUID table to use and update, and
- `output` is the path to a JSON file where the report output should be written to.

To generate and download a report for the inbox of a specific group, add the flag `--inbox <group-name>`.

To generate a new, empty phone number <-> UUID table, use
`$ sh make-new-number-uuid-table.sh <output_path>` where `<output_path>` is a path to a JSON file.
For example `$ sh make-new-number-uuid-table.sh uuid_table.json`.
   
This project is configured to use Python 3.6 by default, but all code is Python 2.7 compliant.

### Configuring Parameters
To change which contact and response fields are downloaded (e.g. "raw, labelled"),
set the `response_formats` and `contact_fields` parameters of the calls
to `session.survey_report_for_name` or `session.inbox_report`.
Refer to the documentation for those functions for the full
list of options.

### Testing
All tests are written in Python's unittest library, and should be runnable solely using the unittest module. However, we recommend using pytest to actually drive the tests. To do this:

1. Run `$ pipenv sync --dev` to install pytest into the project's virtual environment.
2. To run the tests: `$ pipenv run python -m pytest --doctest-modules`.
