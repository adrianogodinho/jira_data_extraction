import datetime as dt

JIRA_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
OUTPUT_DATETIME_FORMAT = '%Y%m%dT%H%M%S'
OUTPUT_DATE_FORMAT = '%Y/%m/%d'


def to_datetime(str_date):
    return dt.datetime.strptime(str_date, JIRA_DATETIME_FORMAT)


def jira_to_simple_date(str_jira_date):
    python_date = to_datetime(str_jira_date)
    return python_date.strftime(OUTPUT_DATE_FORMAT)


def text_to_csv(txt):
    return txt.replace('\n', '\\n').replace('"', '""')
