from encodings import search_function
from multiprocessing.sharedctypes import Value
from sys import api_version
from numpy import double
import streamlit as st
import pandas as pd
import requests
import os
from pprint import pprint
import openai

# Query Azure Cognitive Search
def send_query(search_settings={}, search= "*", search_filters={"search" : None, "filters": None, "booster": None}, select="", searchFields="", semantic=False):
    url = f"https://{search_settings['search_service']}.search.windows.net/indexes/{search_settings['index_name']}/docs/search?api-version={search_settings['api_version']}"

    headers = {
        "content-type" : "application/json",
        "api-key" : search_settings['api_key']
    }

    body = {
        "search" : search if search_filters.get('search') == None else search_filters['search'],
        "facets" : [],
        "count" : True,
        "select" : select,
        "searchMode" : "any",
        "filter" : "" if search_filters['filters'] == None else search_filters['filters']
    }

    if semantic:
        body['queryType'] = 'semantic'
        body['queryLanguage'] = search_settings['query_language']
        body['semanticConfiguration'] = 'search-config'

    if search_filters.get('booster'):
        body['scoringProfile'] = search_settings['scoring_profile']
        body['scoringParameters'] = search_filters['booster']

    if searchFields != "":
        body['searchFields'] = searchFields

    pprint(body)

    r = requests.post(url, headers=headers, json=body)

    if not r.ok:
        r.text
    
    count = r.json()['@odata.count']
    r = pd.DataFrame(r.json()['value'])

    if len(r) > 0:
        for s in body['select'].replace(' ', '').split(','):
            s_full = s.split('/')
            s_0 = s_full[0]
            s_1 = s.split('/')[1] if len(s_full) > 1 else ''
            r[s_0] = r[s_0].apply(lambda x: process_col(x,s_1))


    return r, count

# Get index definition with scoring boosts
def get_scoring_boosts(search_settings={}):
    url = f"https://{search_settings['search_service']}.search.windows.net/indexes/{search_settings['index_name']}?api-version={search_settings['api_version']}"

    headers = {
        "content-type" : "application/json",
        "api-key" : search_settings['api_key']
    }

    # GET https://[service name].search.windows.net/indexes/[index name]?api-version=[api-version]  
    #   Content-Type: application/json  
    #   api-key: [admin key] 

    r = requests.get(url, headers=headers)
    index_data = r.json()

    sp = list(filter(lambda x: x['name'] == 'TagBoosting', index_data['scoringProfiles']))[0]

    boost_scores = {}
    for f in sp['functions']:
        boost_scores[f['fieldName']] = f['boost']

    return boost_scores

# Modify Tag Boosting Scoring Profile
def update_scoring_profile(search_settings={}):
    url = f"https://{search_settings['search_service']}.search.windows.net/indexes/{search_settings['index_name']}?api-version={search_settings['api_version']}"

    headers = {
        "content-type" : "application/json",
        "api-key" : search_settings['api_key']
    }

    # GET https://[service name].search.windows.net/indexes/[index name]?api-version=[api-version]  
    #   Content-Type: application/json  
    #   api-key: [admin key] 

    r = requests.get(url, headers=headers)
    index_data = r.json()

    # PUT https://[search service name].search.windows.net/indexes/[index name]?api-version=[api-version]  
    #   Content-Type: application/json  
    #   api-key: [admin key]

    sp = list(filter(lambda x: x['name'] == 'TagBoosting', index_data['scoringProfiles']))[0]
    for f in sp['functions']:
        f['boost'] = st.session_state[f['fieldName']]

    rr = requests.put(url, headers=headers, json=index_data)

    if rr.ok:
        st.success('Scoring Profile correctly updated.')

# Logic for terms boosting and filtering
def boost_terms(search, terms_similarity, filter_checkboxes, filter_thresholdes, selections_thresholdes, boosting_checkboxes):

    similarity = terms_similarity.to_dict('records')

    res_search = search
    
    # Filters
    filters = ""
    filters_keys = list(filter(lambda x: x['value'], filter_checkboxes))

    # filters_keys

    for fk in filters_keys:
        threshold = list(filter(lambda x: x['key'] == fk['key'], filter_thresholdes))[0]['value']
        select_th = list(filter(lambda x: x['key'] == fk['key'], selections_thresholdes))[0]['value']
        # term = list(filter(lambda x: x['key'] == fk['key'] and double(x['score']) * 100 > double(threshold), similarity))
        term = list(filter(lambda x: x['key'] == fk['key'].split('/')[0].split('_')[0] and double(x['score']) * 100 > double(threshold), similarity))
        term = sorted(term, key = lambda x: x['score'], reverse = True)[0:int(select_th)]

        if len(term) > 0:
            term = ','.join(list(map(lambda x: x['term'], term)))
            if 'Collection' in fk['type']:
                if '/' in fk['key']:
                    fk_name = fk['key'].split('/')[0]
                    fk_sub  = fk['key'].split('/')[1]
                    filters += f"({fk_name}/any(l: search.in(l/{fk_sub}, '{term}')))" if filters == '' else f" and ({fk_name}/any(l: search.in(l/{fk_sub}, '{term}')))"
                else:
                    fk_name = fk['key']
                    filters += f"({fk_name}/any(l: search.in(l, '{term}')))" if filters == '' else f" and ({fk_name}/any(l: search.in(l, '{term}')))"

            elif fk['type'] == "Edm.String":
                filters += f"(search.in({fk['key']},'{term}'))" if filters == '' else f" and (search.in({fk['key']},'{term}'))"
            else:
                fk_name = fk['key'].split('/')[0]
                fk_sub  = fk['key'].split('/')[1]
                filters += f"(search.in({fk_name}/{fk_sub},'{term}'))" if filters == '' else f" and (search.in({fk_name}/{fk_sub},'{term}'))"


    # Boosting
    boosting_keys = list(filter(lambda x: x['value'], boosting_checkboxes))


    # Prevent terms addition if highest terms similarity score is below a threshold
    higher_score = len(list(filter(lambda x: double(x['score']) > 0.90, similarity))) > 0
    booster = []
    for bk in boosting_checkboxes:
        boost_param = bk['key'].split('/')[0].split('_')[0][0:16]
        field_boost = f"{boost_param}-''"
        if bk in boosting_keys:
            threshold = list(filter(lambda x: x['key'] == bk['key'], filter_thresholdes))[0]['value']
            select_th = list(filter(lambda x: x['key'] == bk['key'], selections_thresholdes))[0]['value']
            term = list(filter(lambda x: x['key'] == bk['key'].split('/')[0].split('_')[0] and double(x['score']) * 100 > double(threshold), similarity))
            term = sorted(term, key = lambda x: x['score'], reverse = True)[0:int(select_th)]
            if len(term) > 0:
                term = ",".join(list(map(lambda x: f"'{x['term']}'", term)))
                field_boost += f"{term}" if field_boost == f"{bk['key']}" else f",{term}"
                res_search += f' {term.replace(","," ")}'if term.lower().replace("'",'') not in res_search.lower() and higher_score and 'productName' not in bk['key'] else ''
        booster.append(field_boost)

    return {
        "search" : res_search,
        "filters" : filters,
        "booster" : booster
    }

# Logic for data visualization
def process_col(x, s_1):
    res = []
    if x == None:
        return ''
    if type(x) == list:
        if len(x) == 0:
            return ''
        res = x
    elif type(x) == str:
        return x
    else:
        res.append(x)

    if s_1 != '':
        return ", ".join(list(map(lambda x: x.get('s_1') if x.get('s_1') != None else '', res)))
    else:
        return ", ".join(res)

# Collapse ComplexType fields with additional info
def get_full_field_name(x, complex_type_name, complex_type_type):
    x['main_name'] = complex_type_name
    x['sub_name'] = x['name']
    x['name'] = f"{complex_type_name}/{x['name']}"
    x['main_type'] = complex_type_type
    x['collection_complex_type'] = True if 'Collection' in complex_type_type else False
    return x 

# Extract index fields details
def get_fields_from_index(search_settings):
    # GET https://[service name].search.windows.net/indexes/[index name]?api-version=[api-version]  
    # Content-Type: application/json  
    # api-key: [admin key]

    url = f"https://{search_settings['search_service']}.search.windows.net/indexes/{search_settings['index_name']}?api-version={search_settings['api_version']}"

    headers = {
        "content-type" : "application/json",
        "api-key" : search_settings['api_key']
    }

    r = requests.get(url, headers=headers)
    
    fields = r.json()['fields']

    # Get all Fields and SubFields
    full_fields = []
    for field in fields:
        if field.get('type') in ("Edm.ComplexType", "Collection(Edm.ComplexType)"):
            full_fields += list(map(lambda x: get_full_field_name(x, field.get('name'), field.get('type')), field.get('fields')))
        else:
            full_fields.append(field)
        
    len(full_fields)

    # full_fields

    retrievable = list(filter(lambda x: x.get('retrievable'), full_fields))
    filterable  = list(filter(lambda x: x.get('filterable') , full_fields))
    boostable   = list(filter(lambda x: x.get('type') in ("Edm.String", "Collection(Edm.String)") and not x.get('collection_complex_type'), full_fields))

    types = {}
    for ft in full_fields:
        types[ft['name']] = ft['type'] if not ft.get('collection_complex_type') else f"Collection({ft['type']})"

    return retrievable, filterable, boostable, types


# Get suggested query from OpenAI
def get_open_ai_suggested_query(query):

    default_prompt = "girl yellow cardian -> $search=girl yellow cardigan&$filter=color eq 'Yellow' and productTypeName eq 'Cardigan' and productGender eq 'Female'\nblu man t-shirt -> $search=blu man t-shirt&$filter=color eq 'Blue' and productTypeName eq 'T-shirt' and productGender eq 'Male'\nblack hoodie ->  $search=black hoodie&$filter=color eq 'Black' and productTypeName eq 'Hoodie'\ncotton black pant -> $search=cotton black pant&$filter=color eq 'black' and productTypeName eq 'Black' and productQuality eq 'cotton'\nlight blue cotton polo shirt -> $search=light blue cotton polo shirt&$filter=color eq 'Light Blue' and productQuality eq 'Cotton' and productTypeName eq 'Polo Shirt'\ngreen cashmere polo shirt -> $search=green cashmere polo shirt&$filter=color eq 'Green' and productQuality eq 'Cashmere' and productTypeName eq 'Polo Shirt'\n"
    initial_prompt = os.getenv('gpt3_prompt', default_prompt)

    response = openai.Completion.create(
    engine="text-ada-001",
    prompt= f"{initial_prompt}{query} ->",
    temperature=0,
    max_tokens=64,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop=["#"]
    )

    return response['choices'][0]['text']

########## END - UTILS FUNCTIONS ##########
