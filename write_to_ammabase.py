#! /usr/bin/env python3

from bs4 import BeautifulSoup
import requests
import datetime
import os
import pprint
import pickle
import argparse
import html
import hashlib
import time
import requests
import urllib.parse

USERNAME = 'AMRITAYOGA.AMRITAPURI@AMRITAYOGA.COM'
PASSWORD = 'amma108PATANJAL!'

BASE_URL = 'https://lists.ammagroup.org/'
LOGIN = BASE_URL + 'login.php'
NEW_CAMPAIGN = BASE_URL + 'dbaccess/campaign_update_one_ajax.php'
CAMPAIGN_DATA = {
    'campaign_type': 'NEW',
    'campaign_id': -1,
    'campaign_id_source': -1,
    'grp_id': 377,
    'region_id': '',
    'satsang_id': '',
    'title': 'A',
    'status': 'DRAFT'
}


login_data = {
    'email': USERNAME,
    'password': PASSWORD
}

SESS_FILE = 'session'

def main():
    already_logged_in = False
    if os.path.exists(SESS_FILE):
        session = pickle.load(open(SESS_FILE, 'rb'))
        already_logged_in = True
    else:
        session = requests.Session()
        already_logged_in = False


    # print(dir(cj))
    if not already_logged_in:
        session.post("https://lists.ammagroups.org/login.php", data=login_data)
    else:
        print(session.auth)
        print(session.headers)
        print(dir(session.cookies))
        print(session.cookies.items())


    # campaign_page = session.get('https://lists.ammagroups.org/manage_campaign.php')
    # new_campaign = session.post("https://lists.ammagroups.org/dbaccess/campaign_update_one_ajax.php", data=CAMPAIGN_DATA)
    # print(new_campaign.text)


    # campaign_content = session.post('https://lists.ammagroups.org/campaign_content.php', data={
    #     'campaign_id': 15016,
    #     'status': 'DRAFT',
    #     'from_email': USERNAME,
    #     'from_identity': 'Amrita Yoga Amritapuri',
    #     'group_name': 'AMRITA YOGA',
    #     'campaign_subject': 'A',
    #     'grp_id': 337
    # })

    # print(campaign_content.text)


    # Set value in the editor


    content = '''<html>
<head><meta name="viewport" content="width=650">
	<title></title>
</head>
<body class="vsc-initialized">New content</body>
</html>'''

    quoted_content = urllib.parse.quote(content)

    # update_content = session.post('https://lists.ammagroups.org/dbaccess/campaign_content_update_ajax.php', data={
    #     'campaign_id': 15016,
    #     'content':quoted_content,
    #     'len': len(quoted_content)
    # })

    ofile = open(SESS_FILE, 'wb')
    pickle.dump(session, open(SESS_FILE, 'wb'))
    ofile.close()
    # print(page.text)
    # print(dir(page))
    # login = session.post(LOGIN, data={
    #     'email': USERNAME,
    #     'password': PASSWORD
    # })
    # print(login.text)
    # time.sleep(5)

    #campaign_page = session.get('https://lists.ammagroups.org/manage_campaign.php')
    #print(campaign_page.text)

    #new_campaign_command = session.post(NEW_CAMPAIGN, data=CAMPAIGN_DATA)
    # print(new_campaign_command.text)


main()
