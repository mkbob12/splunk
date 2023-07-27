""" Splunk HEC Input Module"""

import json
import logging
import requests
import urllib3

# SSL Warning 제거
urllib3.disable_warnings()

with open('./conf.json', 'r', encoding='utf-8') as mainconf:
    conf = json.load(mainconf)


SPLUNK_SERVER = conf['splunk']['server']

SPLUNK_HEC_TOKEN = conf['splunk']['token']
SPLUNK_HEADER = {"Authorization":'Splunk ' + SPLUNK_HEC_TOKEN, "Connection": "keep-alive"}
SPLUNK_HEC_URL = f'https://{SPLUNK_SERVER}:8088/services/collector/raw'

#page = requests.get(SPLUNK_HEC_URL, verify=False)

# Create a seesion with keep - alive 
session = requests.Session()
session.verify = False
session.headers.update(SPLUNK_HEADER)


def input_splunk(input_data, filepath=None):
    """Splunk HEC Input"""
    try:
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as input_file:
                input_data = json.load(input_file)
        for i in range(100):
            response = requests.post(SPLUNK_HEC_URL, data=json.dumps(input_data), verify=False,
                                    headers=SPLUNK_HEADER, timeout=10)
            
        if response.status_code == 200:
            return True
        else:
            logging.error(f"Error sending data to Splunk HEC: {response.content}")
            return False
    except Exception as error:
        logging.error(error)
        return False


if __name__ == '__main__':
    test_dict = {'index': 'bob12', 'event':'hello world'}

    input_splunk(test_dict)
