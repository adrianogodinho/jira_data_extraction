from jira import JIRA
import datetime as dt
import jira_import_utils as data_u

API_TOKEN = 'RskOrffizTzxOx9R5bHw85C3'
FILTER_ID = '48993'

WORKFLOW_STATUS = {'10801': 'Product Backlog',      '11010': 'In Development',
                   '13035': 'Approved for SIT',     '12623': 'UAT Done',
                   '12622': 'SIT Done',             '13036': 'Approved for UAT',
                   '11003': 'In Production',        '13011': 'In Technical Analysis',
                   '11204': 'Developed',            '10008': 'Ready For Development',
                   '12799': 'In Business Analysis', '11303': 'Tested',
                   '13009': 'In UI/UX Analysis',    '13010': 'In Data Analysis',
                   '11004': 'Blocked'}

FILE_NAME = 'jira_' + dt.date.today().strftime(data_u.OUTPUT_DATETIME_FORMAT) + '.csv'


def get_time_in_status(jira):

    def calc_time_on_status(status_obj):
        if 'end_time' not in status_obj or 'start_time' not in status_obj or status_obj['end_time'] is None \
                or status_obj['start_time'] is None:
            return -1

        delta = status_obj['end_time'] - status_obj['start_time']
        return delta.days

    def create_object(status_id):
        if status_id not in time_in_status:
            time_in_status[status_id] = {'start_time': None, 'end_time': None, 'duration': -1}

    creation_date = data_u.to_datetime(jira.fields.created)

    time_in_status = {'10801': {'start_time': creation_date, 'end_time': None, 'duration': -1}}

    if jira.changelog.total < 1:
        return time_in_status

    for history in jira.changelog.histories:

        if len(history.items) < 1:
            continue

        for item in history.items:

            if item.field != 'status':
                continue

            from_status_id = getattr(item, 'from')
            to_status_id = item.to

            # The 'from' will always exist, since it is created on time_in_status_declaration.
            create_object(to_status_id)
            create_object(from_status_id)

            # Time in status can be calculated whenever there is a state transition, where I know the start time of the
            # next status and the end time of the previous one.
            history_created = data_u.to_datetime(history.created)
            time_in_status[from_status_id]['end_time'] = history_created
            time_in_status[to_status_id]['start_time'] = history_created

            # If the end_time of the previous one, I can compute their duration. Except if it is the initial state,
            # where the startTime will be always null (that should happen only for the first state).
            time_in_status[from_status_id]['duration'] = calc_time_on_status(time_in_status[from_status_id])
            time_in_status[to_status_id]['duration'] = calc_time_on_status(time_in_status[to_status_id])

    return time_in_status


jclient = JIRA(server='https://ab-inbev.atlassian.net/', basic_auth=('Adriano.Godinho@ab-inbev.com', API_TOKEN))

resultList = jclient.search_issues(jql_str='filter=' + FILTER_ID, expand='changelog')


with open(FILE_NAME, 'w') as out:

    headers = 'key, summary, created, resolution_date, team, state_id, state, start_time, end_time, duration\n'

    out.write(headers)

    for issue in resultList:

        team = "Pricing Engine"

        if issue.fields.customfield_13230 is not None:
            team = issue.fields.customfield_13230.value

        created_date = data_u.to_datetime(issue.fields.created)
        resolution_date = data_u.to_datetime(issue.fields.resolutiondate)

        row = issue.key + ',\"' + issue.fields.summary + '\",' + created_date.strftime(data_u.OUTPUT_DATE_FORMAT) + ',' \
              + resolution_date.strftime(data_u.OUTPUT_DATE_FORMAT) + ',' + team


        state_change_logs = get_time_in_status(issue)

        for state_id in state_change_logs:
            state_dates = state_change_logs[state_id]
            state_row = row + ',' + state_id + ','
            state_row = state_row + (WORKFLOW_STATUS[state_id] if state_id in WORKFLOW_STATUS else 'Unknown') + ','
            state_row = state_row + (state_dates['start_time'].strftime(data_u.OUTPUT_DATE_FORMAT) if state_dates['start_time'] is not None else '') + ','
            state_row = state_row + (state_dates['end_time'].strftime(data_u.OUTPUT_DATE_FORMAT) if state_dates['end_time'] is not None else '') + ','
            state_row = state_row + str(state_dates['duration'])

            out.write(state_row+'\n')
