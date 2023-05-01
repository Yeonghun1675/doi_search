import sys
import requests
import re
from pathlib import Path
import logging
import random
import csv
#from PIL import Image
from io import BytesIO
import json
import pandas as pd
import time

### Hyperparamaeters #########################################
api_key = 'api_key.txt'
query = 'TITLE-ABS-KEY ( metal-organic  AND framework )'

output = 'mof_doi.csv'
sleep = 10
############################################


# GET API KEY
with open(api_key) as f:
    api_key = f.read().strip()
    
    
# My custom logger
def __get_logger(logname):
    __logger = logging.getLogger(logname)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    stream_handler = logging.FileHandler(logname)
    stream_handler.setFormatter(formatter)
    __logger.addHandler(stream_handler)
    __logger.setLevel(logging.DEBUG)
    return __logger
logger = __get_logger('log.txt')    


class DownloadError(Exception):
    """Download Error"""
    def __init__(self, error_code : int):
        """Attributes:
        error_code : status code of requests from url
        """
        
        error_text = {
            400:'Invalid Request: This is an error that occurs when invalid information is submitted.',
            401:'Authentication Error: This is an error that occurs when a user cannot be authenticated due to missing/invalid credentials (authtoken or APIKey).',
            403:'Authorization/Entitlements Error: This is an error that occurs when a user cannot be authenticated or entitlements cannot be validated.',
            404:'Resource Not Found Error: This is an error that occurs when the requested resource cannot be found.',
            405:'Invalid HTTP Method: This is an error that occurs when the requested HTTP Method is invalid.',
            406:'Invalid Mime Type: This is an error that occurs when the requested mime type is invalid.',
            429:'Quota Exceeded: This is an error that occurs when a requester has exceeded the quota limits associated with their API Key.',
            500:'Generic Error: This is a general purpose error condition, typically due to back-end processing errors.'
        }
        
        super().__init__(error_text[error_code])
        
        
def elsevier_search(query, **kwargs):
    """Search image for elsevier journal
    
    Attributes:
        DOI : (str) doi of paper
        ref : (str) Reference of image in XML file. ex) gr1, gr2
        output : (str) output filename. ex) test.xml
    
    Return:
        (str) xml file of paper
    """
    global api_key
    
    URL = 'https://api.elsevier.com/content/search/scopus'
    
    headers = {"X-ELS-APIKey"  : api_key,
              "Accept"          : f'application/json'}
    
    query = { 'query'           : query,
              'count'          : kwargs.get('count', 200),
             **kwargs}
    
    r = requests.get(URL,headers = headers, params=query)
    status = r.status_code
    
    if not status == 200:
        raise DownloadError(r.status_code)
    
    return json.loads(r.text)


def get_info(info):
    global logger, output

    title = info.get('dc:title')
    publication = info.get('prism:publicationName')
    date = info.get('prism:coverDate')
    doi = info.get('prism:doi')
    url = info.get('prism:url')
    
    if not doi:
        logger.info(f'No doi in {title}-{publication}')
        return

    with open(output, 'a', newline='') as f:
        wr = csv.writer(f)
        wr.writerow([doi, url, publication, date, title])

    
def get_doi_from_elsevier_search(query, **kwargs):
    global logger, output

    with open(output, 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['doi', 'url', 'publication', 'date', 'title'])
    
    cursor = '*'
    len_ = 0
    
    while True:
        try:
            search_result = elsevier_search(query=query, 
                                            cursor=cursor, **kwargs)        
            len_ += len(search_result['search-results']['entry'])
            cursor = search_result['search-results']['cursor']['@next']
            entry = search_result['search-results']['entry']
            logger.info(f'DOI search : {len_}')
            
        except KeyboardInterrupt as e:
            logger.info(f'System interrupt : {e}')
            sys.exit(0)
        except DownloadError:
            return
        except Exception as e:
            logger.info(f'{type(e)} : {e}')
        else:
            for info in entry:
                get_info(info)

        time.sleep(sleep)


if __name__ == '__main__':
    total_search = elsevier_search(query=query)
    num = total_search['search-results']['opensearch:totalResults']
    logger.info(f"Total number of papers : {num}")
    
    # download_doi
    logger.info('start!')
    get_doi_from_elsevier_search(query=query)
    logger.info('finished!')
