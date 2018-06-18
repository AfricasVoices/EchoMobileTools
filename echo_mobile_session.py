import time
from datetime import datetime

import requests
import six


class EchoMobileError(Exception):
    """
    Raised when the Echo Mobile server responded to a request with an error.
    """
    pass


class ReportType(object):
    """
    Contains the report types which Echo Mobile can export, and the corresponding ids used by Echo Mobile
    for each report type.
    """
    # These IDs were determined by inspecting the REST calls which the website was making when generating reports.
    InboxReport = 10
    SearchReport = 11
    SurveyReport = 13


class FileType(object):
    """
    Contains the file types which Echo Mobile can export reports to, and the corresponding ids used by Echo Mobile
    for each file type.
    """
    # These IDs were determined by inspecting the REST calls which the website was making when generating reports.
    CSV = 1
    TSV = 5


class EchoMobileSession(object):
    """
    A client-side API for interacting with Echo Mobile servers.
    
    For example, to download a survey report:
    >>> session = EchoMobileSession()
    >>> session.login(<USERNAME>, <PASSWORD>)
    >>> session.use_account_with_name(<ACCOUNT_NAME>)  # Optional for users with only one account
    >>> report = session.survey_report_for_name(<SURVEY_NAME>)
    >>> session.delete_session_background_tasks()  # Removes the report background task from the Echo Mobile website.
    """
    BASE_URL = "https://www.echomobile.org/api/"

    _log_start_time = 0

    def __init__(self, verbose=False):
        """
        :param verbose: Whether to initialise with verbose mode enabled.
        :type verbose: bool
        """
        self.session = requests.Session()
        self.verbose = verbose
        self.background_tasks = set()

    def log(self, message, **log_args):
        if self.verbose:
            six.print_("[{}] {}".format(datetime.now().isoformat(), message), **log_args)

    def log_start(self, message):
        self._log_start_time = time.time()
        self.log(message, end="", flush=True)

    def log_progress(self, message, progress, **log_args):
        if self.verbose:
            six.print_("\r[{}] {} {:.2f}%".format(
                datetime.fromtimestamp(self._log_start_time).isoformat(),
                message, progress),
                **log_args)

    def clear_progress(self):
        if self.verbose:
            six.print_("\r", end="", flush=True)

    def log_done(self):
        print("Done ({0:.3f}s)".format(time.time() - self._log_start_time))

    def login(self, username, password):
        """
        Logs into Echo Mobile using the given user credentials.

        :param username: Echo Mobile user name to use. Probably an email address.
        :type username: str
        :param password: Echo Mobile password.
        :type password: str
        """
        self.log_start("Logging in as '{}'... ".format(username))

        request = self.session.post(self.BASE_URL + "authenticate/simple",
                                    params={"_login": username, "_pw": password,
                                            # auth is a magic API key extracted from
                                            # echomobile.org/dist/src/app.build.js
                                            "auth": "JXEIUOVNQLKJDDHA2J", "populate_session": 1})
        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()

    def accounts(self):
        """
        Returns the list of accounts available to the user who is currently logged in.

        :return: List of available accounts.
        :rtype: list
        """
        self.log_start("Fetching user's accounts... ")

        request = self.session.get(self.BASE_URL + "cms/account/me", params={"with_linked": 1})
        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()

        self.log("  Accounts found for this user:")
        for account in response["linked"]:
            self.log("    " + account["ent_name"])

        return response["linked"]

    def account_key_for_name(self, account_name):
        """
        Returns the key for the account with the name provided.

        :param account_name: Name of the account to retrieve the key for
        :type account_name: str
        :return: Key for account with account_name
        :rtype: str
        """
        matching_accounts = [account for account in self.accounts() if account["ent_name"] == account_name]

        if len(matching_accounts) == 0:
            raise KeyError("Account with account_name '{}' not found".format(account_name))

        account_key = matching_accounts[0]["key"]

        self.log("Key for account '{}' is '{}'".format(account_name, account_key))

        return account_key

    def use_account_with_key(self, account_key):
        """
        Updates this session to use the account that has the given key.

        :param account_key: Key of account to switch to.
        :type account_key: str
        """
        self.log_start("Switching to account '{}'... ".format(account_key))

        request = self.session.post(self.BASE_URL + "authenticate/linked", params={"acckey": account_key})
        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()

    def use_account_with_name(self, account_name):
        """
        Updates this session to use the account that has the given name.

        Equivalent to choosing an account from the User -> Switch Accounts page of Echo Mobile.

        :param account_name: Name of account to switch to.
        :type account_name: str
        """
        self.use_account_with_key(self.account_key_for_name(account_name))

    def groups(self):
        """Returns the list of groups available to the logged in user/account"""
        self.log_start("Fetching available groups... ")

        request = self.session.get(self.BASE_URL + "cms/group")
        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()
        self.log("  Groups found for this user/account:")
        for group in response["groups"]:
            self.log("    " + group["name"])

        return response["groups"]

    def group_key_for_name(self, group_name):
        """
        Returns the key of the group with the given name.

        :param group_name: Name of group to get the key of
        :type group_name: str
        :return: Key of group
        :rtype: str
        """
        groups = self.groups()
        matching_groups = [g for g in groups if g["name"] == group_name]

        if len(matching_groups) == 0:
            raise KeyError("Requested group not found on Echo Mobile (Available groups: " +
                           ",".join(list(map(lambda g: g["name"], groups))) + ")")

        assert len(matching_groups) == 1, "Multiple surveys with name " + group_name

        group_key = matching_groups[0]["key"]

        self.log("Key for group '{}' is '{}'".format(group_name, group_key))

        return group_key

    def surveys(self):
        """
        Returns the list of active surveys available to the logged in user/account.
        """
        self.log_start("Fetching available surveys... ")

        request = self.session.get(self.BASE_URL + "cms/survey")
        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()

        self.log("  Surveys found for this user/account:")
        for survey in response["surveys"]:
            self.log("    " + survey["name"])

        return response["surveys"]

    def survey_key_for_name(self, survey_name):
        """
        Returns the key for the survey with the given name.

        :param survey_name: Name of survey to get the key of
        :type survey_name: str
        :return: Key of survey
        :rtype: str
        """
        surveys = self.surveys()
        matching_surveys = [s for s in surveys if s["name"] == survey_name]

        if len(matching_surveys) == 0:
            raise KeyError("Requested survey not found on Echo Mobile (Available surveys: " +
                           ",".join(list(map(lambda s: s["name"], surveys))) + ")")

        assert len(matching_surveys) == 1, "Multiple surveys with name " + survey_name

        survey_key = matching_surveys[0]["key"]

        self.log("Key for survey '{}' is '{}'".format(survey_name, survey_key))

        return survey_key

    def await_report_generated(self, report_key, poll_interval=2):
        """
        Polls Echo Mobile for the status of a report until it is marked as complete.

        :param report_key: Key of report to poll status of
        :type report_key: str
        :param poll_interval: Time to wait between polling attempts, in seconds.
        :type poll_interval: float
        """
        self.log_start("Waiting for report to generate... ")

        # Status is not documented, but from observation '1' means generating and '3' means successfully generated
        report_status = 1
        while report_status == 1:
            time.sleep(poll_interval)

            request = self.session.get(self.BASE_URL + "cms/backgroundtask")
            response = request.json()

            if not response["success"]:
                raise EchoMobileError(response["message"])

            task = response["tasks"]["report_" + report_key]

            if task["total"] != 0:
                progress = task["progress"] / task["total"] * 100
                self.log_progress("Waiting for report to generate... ", progress, end="", flush=True)

            report_status = task["status"]

        self.clear_progress()
        self.log("Waiting for report to generate... ", end="", flush=True)
        self.log_done()

        assert report_status == 3, "Report stopped generating, but with an unknown status"

    def generate_survey_report(self, survey_key, response_formats=None, contact_fields=None, wait_until_generated=True):
        """
        Starts the generation of a report for the given survey on Echo Mobile.

        Note that this function only triggers the generation of a report. Completed reports must be downloaded with
        download_survey_report.

        :param survey_key: Key of survey to generate report for.
        :type survey_key: str
        :param response_formats: List of response formats to download. Defaults to ["raw", "label"] if None.
                                 The full list of options is : raw, label, value, score.
        :type response_formats: list of str
        :param contact_fields: List of contact fields to download. Defaults to ["name", "phone"] if None.
                               The full list of options is: name, phone, internal_id, group, referrer, referrer_phone,
                               upload_date, last_survey_complete_date, geo, locationTextRaw, labels, linked_entity,
                               opted_out.
        :type contact_fields: list of str
        :param wait_until_generated: Whether to wait for the report to finish generating on the Echo Mobile server
                                     before returning.
        :type wait_until_generated: bool
        :return: Key of report being generated
        :rtype: str
        """
        if response_formats is None:
            response_formats = ["raw", "label"]
        if contact_fields is None:
            contact_fields = ["name", "phone"]

        self.log_start("Requesting generation of report for survey '{}'... ".format(survey_key))

        request = self.session.post(self.BASE_URL + "cms/report/generate",
                                    params={"type": ReportType.SurveyReport, "ftype": FileType.CSV,
                                            "target": survey_key,
                                            "gen": ",".join(response_formats),
                                            "std_field": ",".join(contact_fields)
                                            }
                                    )
        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()

        report_key = response["rkey"]
        self.background_tasks.add("report_" + report_key)

        if wait_until_generated:
            self.await_report_generated(report_key)

        return report_key

    def generate_inbox_report(self, group_key=None, contact_fields=None, wait_until_generated=True):
        """
        Generates a report containing the messages in an account's inbox.

        Note that this function only triggers the generation of a report. Completed reports must be downloaded with
        download_survey_report.

        :param group_key: Key of group to generate report for.
                          If None, generates a report for the account's global inbox.
        :type group_key: str
        :param contact_fields: List of additional contact fields to download.
                               Defaults to ["group", "upload_date"] if None.
                               "Sender" and "Phone" are always downloaded.
                               The full list of options is: internal_id, group, referrer, upload_date,
                               last_survey_complete_date, geo, locationTextRaw, labels
        :type contact_fields: list of str
        :param wait_until_generated: Whether to wait for the report to finish generating on the Echo Mobile server
                                     before returning.
        :type wait_until_generated: bool
        :return: Key of report being generated
        :rtype: str
        """
        if contact_fields is None:
            contact_fields = ["group", "upload_date"]

        if group_key is None:
            self.log_start("Requesting generation of report for global inbox... ")

            request = self.session.post(self.BASE_URL + "cms/report/generate",
                                        params={
                                            "type": ReportType.SearchReport, "ftype": FileType.CSV,
                                            "std_field": ",".join(contact_fields)
                                        })
        else:
            self.log_start("Requesting generation of report for inbox '{}'... ".format(group_key))

            request = self.session.post(self.BASE_URL + "cms/report/generate",
                                        params={
                                            "type": ReportType.InboxReport, "ftype": FileType.CSV,
                                            "target": group_key,
                                            "std_field": ",".join(contact_fields)
                                        })

        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()

        report_key = response["rkey"]
        self.background_tasks.add("report_" + report_key)

        if wait_until_generated:
            if group_key is None:
                self.log("About to wait for an inbox report to generate. "
                         "Note that progress will always report 0% until done, due to an Echo Mobile bug.")
            self.await_report_generated(report_key)

        return report_key

    def download_report(self, report_key):
        """
        Downloads the specified report from Echo Mobile.

        Note that reports must first be generated before they can be downloaded.

        :param report_key: Key of report to download
        :type report_key: str
        :return: CSV containing the survey report
        :rtype: str
        """
        self.log_start("Downloading report... ")

        request = self.session.get(self.BASE_URL + "cms/report/serve", params={"rkey": report_key})
        response = request.text

        self.log_done()

        return response

    def survey_report_for_key(self, survey_key, contact_fields=None, response_formats=None):
        """
        Generates and downloads a report for the survey with the given key.

        :param survey_key: Key of survey to generate and download report for
        :type survey_key: str
        :param response_formats: List of response formats to download. Defaults to ["raw", "label"] if None.
                                 The full list of options is : raw, label, value, score.
        :type response_formats: list of str
        :param contact_fields: List of contact fields to download. Defaults to ["name", "phone"] if None.
                               The full list of options is: name, phone, internal_id, group, referrer, referrer_phone,
                               upload_date, last_survey_complete_date, geo, locationTextRaw, labels, linked_entity,
                               opted_out.
        :type contact_fields: list of str
        :return: CSV containing the survey report
        :rtype: str
        """
        report_key = self.generate_survey_report(survey_key, contact_fields=contact_fields,
                                                 response_formats=response_formats, wait_until_generated=True)
        return self.download_report(report_key)

    def survey_report_for_name(self, survey_name, contact_fields=None, response_formats=None):
        """
        Generates and downloads a report for the survey with the given name.

        :param survey_name: Name of survey to generate and download report for
        :type survey_name: str
        :param response_formats: List of response formats to download. Defaults to ["raw", "label"] if None.
                                 The full list of options is : raw, label, value, score.
        :type response_formats: list of str
        :param contact_fields: List of contact fields to download. Defaults to ["name", "phone"] if None.
                               The full list of options is: name, phone, internal_id, group, referrer, referrer_phone,
                               upload_date, last_survey_complete_date, geo, locationTextRaw, labels, linked_entity,
                               opted_out.
        :type contact_fields: list of str
        :return: CSV containing the survey report
        :rtype: str
        """
        return self.survey_report_for_key(self.survey_key_for_name(survey_name), contact_fields=contact_fields,
                                          response_formats=response_formats)

    def global_inbox_report(self, contact_fields=None):
        """
        Generates and downloads a report for the current account's global inbox.

        :param contact_fields: List of additional contact fields to download.
                               Defaults to ["group", "upload_date"] if None.
                               "Sender" and "Phone" are always downloaded.
                               The full list of options is: internal_id, group, referrer, upload_date,
                               last_survey_complete_date, geo, locationTextRaw, labels
        :type contact_fields: list of str
        :return: CSV containing the inbox report
        :rtype: str
        """
        return self.download_report(
            self.generate_inbox_report(contact_fields=contact_fields, wait_until_generated=True))

    def group_inbox_report_for_key(self, group_key, contact_fields=None):
        """
        Generates and downloads an inbox report for the group with the given key.

        :param group_key: Key of group to download inbox of
        :type group_key: str
        :param contact_fields: List of additional contact fields to download.
                               Defaults to ["group", "upload_date"] if None.
                               "Sender" and "Phone" are always downloaded.
                               The full list of options is: internal_id, group, referrer, upload_date,
                               last_survey_complete_date, geo, locationTextRaw, labels
        :type contact_fields: list of str
        :return: CSV containing the inbox report
        :rtype: str
        """
        report_key = self.generate_inbox_report(group_key=group_key,
                                                contact_fields=contact_fields, wait_until_generated=True)
        return self.download_report(report_key)

    def group_inbox_report_for_name(self, group_name, contact_fields=None):
        """
        Generates and downloads an inbox report for the group with the given name.

        :param group_name: Name of group to download inbox of
        :type group_name: str
        :param contact_fields: List of additional contact fields to download.
                               Defaults to ["group", "upload_date"] if None.
                               "Sender" and "Phone" are always downloaded.
                               The full list of options is: internal_id, group, referrer, upload_date,
                               last_survey_complete_date, geo, locationTextRaw, labels
        :type contact_fields: list of str
        :return: CSV containing the inbox report
        :rtype: str
        """
        return self.group_inbox_report_for_key(self.group_key_for_name(group_name), contact_fields=contact_fields)

    def inbox_report(self, group_name=None, contact_fields=None):
        """
        Generates and downloads an inbox report.

        :param group_name: Name of group to download inbox of. If None, downloads from the global inbox.
        :type group_name: str
        :param contact_fields: List of additional contact fields to download.
                               Defaults to ["group", "upload_date"] if None.
                               "Sender" and "Phone" are always downloaded.
                               The full list of options is: internal_id, group, referrer, upload_date,
                               last_survey_complete_date, geo, locationTextRaw, labels
        :type contact_fields: list of str
        :return: CSV containing the inbox report
        :rtype: str
        """
        if group_name is None:
            return self.global_inbox_report(contact_fields=contact_fields)
        else:
            return self.group_inbox_report_for_name(group_name, contact_fields=contact_fields)

    def delete_background_task(self, task_key):
        """
        Deletes the background task on Echo Mobile that has the given key.

        :param task_key: Key of background task to delete
        :type task_key: str
        """
        self.log_start("Deleting background task '{}'... ".format(task_key))

        request = self.session.post(self.BASE_URL + "cms/backgroundtask/cancel", params={"key": task_key})
        response = request.json()

        if not response["success"]:
            raise EchoMobileError(response["message"])
        self.log_done()

    def delete_session_background_tasks(self):
        """
        Deletes all the background tasks on Echo Mobile which have been generated by this session so far.
        """
        for key in list(self.background_tasks):
            self.delete_background_task(key)
            self.background_tasks.remove(key)
