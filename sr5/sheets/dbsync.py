
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def fill_defaults(result, length):
    for i in range(0, length):
        if i + 1 > len(result):
            result += [""]

    return result

def main():
    """Shows basic usage of the Sheets API.

    https://developers.google.com/sheets/api/quickstart/python
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    spreadsheetId = '1IgOcna1hLMRZwl0Zy6lC_XArWmQIMEvZNDmbOwGBaw4'

    # Skills
    groups = {}
    categories = {}
    attr = {}

    # Get active skills.
    rangeName = 'Skills!A2:H'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    active = ""

    if not values:
        print('Active Skills: No data found.')
    else:
        print('Active Skills: Doing it!')
        for row in values:
            row = fill_defaults(row, 8)
            active += '\t\t"%s": {\n\t\t\t"attribute": "%s", "default": "%s",\n\t\t\t"group": "%s", "category": "%s",\n\t\t\t"description": "%s",\n\t\t\t"specs": "%s",\n\t\t\t"source": "%s"\n\t\t},\n' % (row[0].lower(), row[1].lower(), row[2].lower(), row[3].lower(), row[4].lower(), row[5], row[6], row[7])

            # Populate groups dict.
            if row[3] and row[3].lower() != "none":
                groups.setdefault(row[3].lower(), [])
                groups[row[3].lower()] += [row[0].lower()]
            # Populate categories dict.
            if row[4] and row[4].lower() != "none":
                categories.setdefault(row[4].lower(), [])
                categories[row[4].lower()] += [row[0].lower()]
            # Populate attributes dict.
            if row[1] and row[1].lower() != "none":
                attr.setdefault(row[1].lower(), [])
                attr[row[1].lower()] += [row[0].lower()]

    # Get knowledge and language skills.
    rangeName = 'Skills!J2:O'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    knowledge = ""

    if not values:
        print('Knowledge/Language Skills: No data found.')
    else:
        print('Knowledge/Language Skills: Doing it!')
        for row in values:
            row = fill_defaults(row, 8)
            knowledge += '\t\t"%s": {\n\t\t\t"attribute": "%s", "default": "%s",\n\t\t\t"description": "%s",\n\t\t\t"specs": "%s",\n\t\t\t"source": "%s"\n\t\t},\n' % (row[0].lower(), row[1].lower(), row[2].lower(), row[3], row[4], row[5])

            # Populate attributes dict.
            if row[1] and row[1].lower() != "none":
                attr.setdefault(row[1].lower(), [])
                attr[row[1].lower()] += [row[0].lower()]

    # Generate the storage document.
    skills_data = open("../data/skills.py", "w+")

    skills_data.write('class Skills():\n'\
                      '\t"""\n'\
                      '\tThis class has been automatically generated based on a Google sheet.\n'\
                      '\t"""\n')

    skills_data.write('\tactive = {\n')
    skills_data.write(active)
    skills_data.write('\t}\n\n')
    skills_data.write('\tknowledge = {\n')
    skills_data.write(knowledge)
    skills_data.write('\t}')

    skills_data.write('\n')
    skills_data.write('\tgroups = ' + str(groups) + '\n')
    skills_data.write('\tcategories = ' + str(categories) + '\n')
    skills_data.write('\tattr = ' + str(attr) + '\n')

if __name__ == '__main__':
    main()
