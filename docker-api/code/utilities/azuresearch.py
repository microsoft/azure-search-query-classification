import requests, os, logging
import utilities.utils as utils
from math import ceil

# Get logging options:
logger = logging.getLogger(__name__)

# Load data in an Azure Cognitive Search index
def push_data_to_search(search_settings={}, path=os.getcwd()):
    url = f"https://{search_settings['search_service']}.search.windows.net/indexes/{search_settings['index_name']}/docs/index?api-version={search_settings['api_version']}"

    headers = {
        "content-type" : "application/json",
        "api-key" : search_settings['api_key']
    }

    # POST https://[service name].search.windows.net/indexes/[index name]/docs/index?api-version=[api-version]   
    #   Content-Type: application/json   
    #   api-key: [admin key]

    data = utils.extract_all_catalog(path)

    for d in data:
        d['@search.action'] = 'upload'
        for k,v in d.items():
            if v == None:
                d[k] = ''
            if type(v) == list and len(v) > 0:
                if v[0] == None:
                    d[k][0] = ''

    data = sorted(data, key=lambda x:x['articleId'])

    batch_size = 1000
    for i in range(0, ceil(len(data)/batch_size)):
            
        body = {
            "value" : list(map(lambda x: x, data[batch_size*i: batch_size*(i+1)]))
        }


        r = requests.post(url, headers=headers, json=body)

        if not r.ok:
            raise ValueError(f"Error in pushing batch {i}. {r.text}")
        
    return True
  
# Create index
def create_index(search_settings={}, data_path=''):
    url = f"https://{search_settings['search_service']}.search.windows.net/indexes/{search_settings['index_name']}?api-version={search_settings['api_version']}"

    headers = {
        "content-type" : "application/json",
        "api-key" : search_settings['api_key']
    }

    # PUT https://[search service name].search.windows.net/indexes/[index name]?api-version=[api-version]  
    #   Content-Type: application/json  
    #   api-key: [admin key]

    index_data = utils.read_json_file(data_path)

    rr = requests.put(url, headers=headers, json=index_data)

    if not rr.ok:
        logging.info(f"Index creation error {rr.text}")
        return rr.text 
    else:
        logging.info(f"Index created successfully {rr.status_code}")
        return rr.status_code