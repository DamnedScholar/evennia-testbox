
from __future__ import print_function
import autopep8
from collections import OrderedDict
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
    credential_path = os.path.join(
        credential_dir, 'sheets.googleapis.com-python-quickstart.json'
    )

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def fill_defaults(result, length):
    "Empty cells will be represented by empty values."
    for i in range(0, length):
        if i + 1 > len(result):
            result += [""]

    return result


def space(n):
    "Insert n spaces here."
    output = ""
    for i in range(0, n):
        output += " "

    return output


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
    groups, categories, attr = {}, {}, {}

    # Get priority values.
    rangeName = 'Priorities!B3:F4'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    priorities = "{"

    values = zip(map(int, values[0]), map(int, values[1]))
    values = dict(zip("abcde", values))
    for pri in "abcde":
        priorities += "'{}': {},".format(pri, values[pri])

    priorities += "}"

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
            row = map(str, row)
            active += '%s"%s": ' \
                      '{\n%s"attribute": "%s", "default": "%s",\n' \
                      '%s"group": "%s", "category": "%s",\n' \
                      '%s"description": "%s",\n' \
                      '%s"specs": "%s",\n' \
                      '%s"source": "%s"\n' \
                      '%s},\n' % (
                        space(8), row[0].lower(),
                        space(12), row[1].lower(), row[2].lower(),
                        space(12), row[3].lower(), row[4].lower(),
                        space(12), row[5],
                        space(12), row[6],
                        space(12), row[7],
                        space(8))

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

    # Get knowledge skills.
    rangeName = 'Skills!J2:O5'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    knowledge = ""

    if not values:
        print('Knowledge Skills: No data found.')
    else:
        print('Knowledge Skills: Doing it!')
        for row in values:
            row = fill_defaults(row, 8)
            row = map(str, row)
            knowledge += '%s"%s": ' \
                         '{\n%s"attribute": "%s", "default": "%s",\n' \
                         '%s"description": "%s",\n' \
                         '%s"specs": "%s",\n' \
                         '%s"source": "%s"\n' \
                         '%s},\n' % (
                           space(8), row[0].lower(),
                           space(12), row[1].lower(), row[2].lower(),
                           space(12), row[3],
                           space(12), row[4],
                           space(12), row[5],
                           space(8))

            # Populate attributes dict.
            if row[1] and row[1].lower() != "none":
                attr.setdefault(row[1].lower(), [])
                attr[row[1].lower()] += [row[0].lower()]

    # Get language skill.
    rangeName = 'Skills!J7:O7'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    language = ""

    for row in values:
        row = fill_defaults(row, 8)
        row = map(str, row)
        language += '%s"%s": ' \
                     '{\n%s"attribute": "%s", "default": "%s",\n' \
                     '%s"description": "%s",\n' \
                     '%s"specs": "%s",\n' \
                     '%s"source": "%s"\n' \
                     '%s},\n' % (
                       space(8), row[0].lower(),
                       space(12), row[1].lower(), row[2].lower(),
                       space(12), row[3],
                       space(12), row[4],
                       space(12), row[5],
                       space(8))

        # Populate attributes dict.
        if row[1] and row[1].lower() != "none":
            attr.setdefault(row[1].lower(), [])
            attr[row[1].lower()] += [row[0].lower()]

    # Get languages.
    rangeName = 'Languages!A1:B'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    for row in values:
        language += '"%s": [%s],\n' % (row[0], row[1])

    rangeName = 'Languages!D1:E'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    language += '"secret": {'

    for row in values:
        language += '"%s": [%s],\n' % (row[0], row[1])

    language += '}\n\n'

    # Generate the storage document.
    skills_data = open("../data/skills.py", "w+")

    output = 'class Skills():\n' \
             '    """\n' \
             '    This class has been automatically generated based on a ' \
             'Google sheet.\n' \
             '    """\n'

    output += '    priorities = ' \
              '{}\n\n'.format(priorities)

    output += '    active = {\n'
    output += '{}'.format(active)
    output += '    }\n\n'
    output += '    knowledge = {\n'
    output += '{}'.format(knowledge)
    output += '    }\n\n'
    output += '    language = {\n'
    output += '{}'.format(language)
    output += '    }\n\n'

    output += '    groups = {}\n\n'.format(groups)
    output += '    categories = {}\n\n'.format(categories)
    output += '    attr = {}\n\n'.format(attr)

    skills_data.write(autopep8.fix_code(output,
                                        options={'aggressive': 3}))

if __name__ == '__main__':
    main()
