from jira import JIRA
import datetime as dt
import jira_import_utils as ju
import re

# Token that can be generated on Jira
API_TOKEN = 'API_TOKEN'

# Id of the filter used to filter the Tickets that will be scanned.
FILTER_ID = '49822'

## Users that will be scanned
## <jira-id> : <name you want on script output>
JIRA_ACCOUNT_ID_MAP = {
    "62b9ed1dfa171a27239ca814": "Adriano Godinho",
}


class JIRABEESOEExtractor:

    def __init__(self):
        self.client = JIRA(server='https://ab-inbev.atlassian.net/',
                           basic_auth=('Adriano.Godinho@ab-inbev.com', API_TOKEN))
        self.mention_pattern = re.compile('\[\~accountid:(.+)\]', re.IGNORECASE)
        self.page_size = 50
        self.last_page_size = -1

    def has_more(self):
        return self.last_page_size != 0

    def get_last_page_size(self):
        return self.last_page_size

    def extract(self, page):

        resultlist = self.client.search_issues(jql_str='filter=' + FILTER_ID, maxResults=self.page_size,
                                               startAt=page * self.page_size)

        self.last_page_size = len(resultlist)

        result_processed = {}

        for jira in resultlist:

            pricing_mentions = self.extract_pricing_mentions(jira)

            if len(pricing_mentions) > 0:
                result_processed[jira.key] = {'jira_obj': jira, 'mentions': pricing_mentions}

        return result_processed

    def extract_row(self, jira):
        return ""

    def extract_pricing_mentions(self, jira):

        pricing_mentions = {}

        for comment in jira.fields.comment.comments:

            accountIdList = re.findall(self.mention_pattern, comment.body)

            for accountId in accountIdList:

                if accountId not in JIRA_ACCOUNT_ID_MAP:
                    continue

                pricing_mentions[accountId] = pricing_mentions[accountId] + 1 if accountId in pricing_mentions else 1

        return pricing_mentions


class JIRADataPersist:

    def persist_jira_processed_data(self, jira_processed_data):

        file_name = "jira_mentions" + dt.date.today().strftime(ju.OUTPUT_DATETIME_FORMAT) + ".csv"

        with open(file_name, 'a') as file:

            for jira_key in jira_processed_data:

                jira_item = jira_processed_data[jira_key]
                jira_obj = jira_item['jira_obj']
                mentions = jira_item['mentions']

                row = jira_key + ',\"' + jira_obj.fields.summary + '\",\"' + ju.text_to_csv(
                    jira_obj.fields.description) + '\",' + \
                      ju.jira_to_simple_date(jira_obj.fields.created)

                for account_id in mentions:
                    account_row = row + ',' + JIRA_ACCOUNT_ID_MAP[account_id]
                    file.write(account_row + '\n')


contentExtractor = JIRABEESOEExtractor()
contentPersistent = JIRADataPersist()

page = 0

total_scanned = 0
total_found = 0

while contentExtractor.has_more():
    result_processed = contentExtractor.extract(page)
    contentPersistent.persist_jira_processed_data(result_processed)

    total_scanned = total_scanned + contentExtractor.get_last_page_size()
    total_found = total_found + len(result_processed)
    page = page+1

    print(f"Found {total_found} from {total_scanned} scanned ticket")


