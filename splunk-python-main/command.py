import sys
import time
import json
import requests 
from splunklib.searchcommands import dispatch, GeneratingCommand, Option,Configuration
import virustotal3.core

@Configuration()
class VirusTotalSearchCommand(GeneratingCommand):
    """A custom search command that returns the results of a VirusTotal search"""
    q = Option(require=True)

    # event 생성 
    def generate(self):
        api_key = 'c786b2c9c61744e3c1c79ab89007e7f951083257237ed84d59aab21b3eba1fcd'

        # AUBSELPDB 
        abuse_api_key = '51b7af44a1399effbfeb6be17a807bac202ba073a37a9191b8431807daffa406aaa4c082c7d712be'
        
        #list of cti platforms to query 
        virus_total = virustotal3.core.IP(api_key=api_key)
        
        # List of CTI platforms to query
        cti_platforms = ["Virustotal", "AbseIpDB"]

        try:
            result = virus_total.info_ip(self.q)

            yield self.get_event(result['data'])

        except Exception as error: # pylint: disable=broad-except
            self.get_event({'error': 'No result from virustotal with error: '
                            + str(error) + ' for query: ' + self.q + ''})
        
        try:
            result = self.query_abuseipdb(abuse_api_key, self.q)

            yield self.get_event(result['data'])

        except Exception as error: # pylint: disable=broad-except
            self.get_event({'error': 'No result from virustotal with error: '
                            + str(error) + ' for query: ' + self.q + ''})
    
    


    def query_abuseipdb(self, api_key, ip_address):
        # Implement your AbseIpDB API query logic here
        # Replace the following lines with your AbseIpDB API call
        url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip_address}"
        headers = {
            "Key": api_key,
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        return response.json()
    
    
    # splunk 화면에 결과를 출력한다. 
    def get_event(self, result):
        """Return an event"""
        event = result
        event['_time'] = time.time()
        event['_raw'] = json.dumps(result)
        return event

dispatch(VirusTotalSearchCommand, sys.argv, sys.stdin, sys.stdout, __name__) # pylint: disable=abstract-class-instantiated
