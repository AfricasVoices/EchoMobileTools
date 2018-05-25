# Echo Mobile Experiments
Includes `fetch_runs.py`, which downloads the results of an EchoMobile survey and emits them to a JSON file of
TracedData objects.

## Usage
1. Install Pipenv.

1. Install dependencies: `$ pipenv sync`

1. Run with
   `$ pipenv run python fetch_report.py <echo-mobile-username> <echo-mobile-password> <user> <survey-name> <output>`.
   For more detail on the arguments, run `$ pipenv run python fetch_report.py --help`.
