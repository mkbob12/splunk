'''
Splunk Query
Splunk 서버에 접속하여 검색을 수행하고, 결과를 파일로 저장하는 모듈
'''
import os
import time
import json
import urllib
from datetime import datetime
from xml.dom import minidom
import logging
import requests
import pandas as pd

import urllib3

# SSL Warning 제거
urllib3.disable_warnings()

with open('./conf.json', 'r', encoding='utf-8') as mainconf:
    conf = json.load(mainconf)

SPLUNK_SERVER = conf['splunk']['server']

SPLUNK_USERNAME = conf['splunk']['username']

SPLUNK_PASSWORD = conf['splunk']['password']

FILE_PATH = './'

# Create a session with keep-alive
session = requests.Session()
session.verify = False

def search_splunk(sp_qeury, file_save = False):
    """Splunk Query"""
    if not sp_qeury.startswith('search'):
        sp_qeury = 'search ' + sp_qeury
    try:
        share_url = ''
        sp_search_count = 0
        #Step 1: Get a session key
        splunk_url = f'https://{SPLUNK_SERVER}:8089'
        server_content = requests.post(splunk_url + '/services/auth/login',
            data=urllib.parse.urlencode({'username':SPLUNK_USERNAME, 'password':SPLUNK_PASSWORD}),
            verify=False, timeout=10)
        session_key = minidom.parseString(server_content.text).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
        time.sleep(1)
        #Step 2: Create a search job
        es_url = f'{splunk_url}/services/search/jobs'
        session_headers = {'Authorization': f'Splunk {session_key}'}
        
    
        
        search_respone = requests.post(es_url+'', data=urllib.parse.urlencode({'search': sp_qeury}),
            headers = session_headers,
            verify = False, timeout=10)
        sid = minidom.parseString(search_respone.text).getElementsByTagName('sid')[0].firstChild.nodeValue
        time.sleep(1)
        isnotdone = True
        while isnotdone:
            es_url = f'{splunk_url}/services/search/jobs/{sid}'
            search_respone = requests.get(es_url,
                headers=session_headers,
                verify = False, timeout=10)
            response = minidom.parseString(search_respone.text)
            for node in response.getElementsByTagName("s:key"):
                if node.hasAttribute("name") and node.getAttribute("name") == "dispatchState":
                    dispatch_state = node.firstChild.nodeValue
                    if dispatch_state == "DONE":
                        isnotdone = False
                        time.sleep(1)
                        break
                    else:
                        time.sleep(3)
        #검색 결과가 나왔을때, 실제 카운트를 찾음
        for node in response.getElementsByTagName("s:key"):
            if node.hasAttribute("name") and node.getAttribute("name") == "eventCount":
                sp_search_count = int(node.firstChild.nodeValue)
                break
        es_url = f'{splunk_url}/services/search/jobs/{sid}/results/?output_mode=json&count=50000'
        search_respone = requests.get(es_url, headers=session_headers,
                                      verify=False, timeout=10)
        jsondata = json.loads(search_respone.text)
        logcount = len(jsondata['results'])
        offset = logcount
        time.sleep(1)
        df_result = pd.DataFrame(jsondata['results'])
        if logcount != 0:
            keep_run = True
            while keep_run:
                if logcount != 50000:
                    keep_run = False
                es_url = f'{splunk_url}/services/search/jobs/{sid}/results/?output_mode=json&count={sp_search_count}&offset={offset}'
                search_respone = requests.get(es_url, headers=session_headers,
                                              verify=False, timeout=10)
                jsondata = json.loads(search_respone.text)
                logcount = len(jsondata['results'])
                df_add = pd.DataFrame(jsondata['results'])
                df_result = pd.concat([df_result, df_add])
                offset = offset+logcount
            task_date = datetime.now()
            sp_file_path = ''
            if file_save:
                directory = FILE_PATH+str(task_date.month)+'/'
                if not os.path.exists(os.path.dirname(directory)):
                    os.makedirs(os.path.dirname(directory))
                sp_search_filename = 'splunk_query.xlsx'
                sp_file_path = os.path.join(directory, sp_search_filename)
                df_result.to_excel(sp_file_path)
            if offset != 0:
                # 검색 결과 공유
                es_url = f'{splunk_url}/services/search/jobs/{sid}/acl'
                search_respone = requests.post(es_url+'', headers=session_headers,
                                               data=urllib.parse.urlencode({'perms.read': '*'}),
                                               verify=False, timeout=10)
            sp_search_result = True
    except Exception as sp_search_e: # pylint: disable=broad-except
        sp_search_error = str(sp_search_e)
        sp_search_result = False
        logging.warning('sp_search_error: %s', sp_search_error)
        time.sleep(1)
    return sp_search_result, df_result.to_json(), offset, share_url, sp_file_path

if __name__ == '__main__':
    search_result,  json_result, conut_result, url_result, filepath_result = search_splunk('index="bob12" | head 10', file_save = True)
    print('search_result: \n\n ',search_result)
    print('json_result: \n\n ',json_result)
    print('conut_result: \n\n ',conut_result)
    print('filepath_result: \n\n ',filepath_result)
    print('url_result: \n\n ',url_result)