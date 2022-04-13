import streamlit as st
import pandas as pd
from urllib.error import URLError
import requests, os, openai
from utilities import utils
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("local_run", nargs='?', default=False)

args = parser.parse_args()

if args.local_run:    
    from dotenv import load_dotenv
    load_dotenv('../../.env')
    os.environ["prod_url"] = "http://localhost:8000"

try:
    # Set page layout to wide screen and menu item
    menu_items = {
	'Get help': None,
	'Report a bug': None,
	'About': '''
	 ## Embeddings App

	 Embedding testing application.
	'''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

    supported_models = ['msmarco-distilbert-dot-v5', 'all-mpnet-base-v2', 'nq-distilbert-base-v1', 'all-MiniLM-L6-v2', 'curie-search-query-msft', 'babbage-search-query-msft', 'ada-search-query-msft']
    default_select = os.getenv('select')
    default_searchFields =  os.getenv('searchFields')

    # Read ENV settings
    select = os.getenv('select')
    if select == None:
        raise ValueError(f"No value provided for ENV Variable 'select'. Please insert fields selection")

    models = os.getenv('SentenceTransformer','')
    models += f",{os.getenv('GPT_3')}" if os.getenv('GPT_3','') != '' else ''
    models = models.replace(' ','').split(',')
    if models == None:
        raise ValueError(f'Model name has to be in the following list: {models}')
    for m in models:
        if m not in supported_models:
            raise ValueError(f'Model name has to be in the following list: {models}')

    base_url = os.getenv('prod_url')
    if base_url == None:
        raise ValueError(f"No value provided for ENV Variable 'base_url'. Please insert embedding API base URL")

    search_settings = {}
    search_settings['search_service'] = os.getenv('search_service')
    if search_settings['search_service'] == None:
        raise ValueError(f"No value provided for ENV Variable 'search_service'.")

    search_settings['index_name'] = os.getenv('index_name')
    if search_settings['index_name'] == None:
        raise ValueError(f"No value provided for ENV Variable 'index_name'.")
    
    search_settings['api_version'] = os.getenv('api_version')
    if search_settings['api_version'] == None:
        raise ValueError(f"No value provided for ENV Variable 'api_version'.")
    
    search_settings['api_key'] = os.getenv('api_key')
    if search_settings['api_key']  == None:
        raise ValueError(f"No value provided for ENV Variable 'api_key'.")

    search_settings['query_language']  = os.getenv('query_language', 'en-US')
    search_settings['scoring_profile'] = os.getenv('scoring_profile', 'TagBoosting')

    prod_url = os.getenv('prod_url')
    if prod_url == None:
        raise ValueError(f"No value provided for ENV Variable 'prod_url'.")

    boost = os.getenv('boost')
    if boost == None:
        raise ValueError(f"No value provided for ENV Variable 'boost'.")

    filters = os.getenv('filters')

    openai.api_key = os.getenv('OPENAI_API_KEY')

    if prod_url != None:
        try:  
            r = requests.get(f"{os.getenv('prod_url')}/ready")
        except:
            st.error('API still loading. Please wait few minutes and refresh the page...')

    # MAIN Page

    # Get fields from index
    retrievable, filterable, boostable, types = utils.get_fields_from_index(search_settings)

    # Field selection
    selections = select.replace(' ','').split(',')

    # Boost
    st.sidebar.title("Boosting")
    boost_selections = list(filter(lambda x: x in list(map(lambda x: x['name'], boostable)), selections))
    boost_selections = list(filter(lambda x: x in boost.replace(' ','').split(','), boost_selections))
    boosts_values = utils.get_scoring_boosts(search_settings)

    # boost_selections
    boosting_checkboxes  = list(map(lambda x: {"key": x, "value" : st.sidebar.checkbox(f"Boost {x}")}, boost_selections))

    # Configuration
    with st.expander("Configuration"):
        fe_select           = st.text_input('select', value = default_select) 
        fe_searchFields     = st.text_input('searchFields', value = default_searchFields) 
        st.write('Boosting values')
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            boosting_values  = list(map(lambda x: {"key": x, "value" : st.number_input(f"{x}", value=boosts_values[x], min_value=0.01, on_change=utils.update_scoring_profile, args=search_settings, key=x)}, boost_selections[0:3]))
        with col2:
            boosting_values += list(map(lambda x: {"key": x, "value" : st.number_input(f"{x}", value=boosts_values[x], min_value=0.01, on_change=utils.update_scoring_profile, args=search_settings, key=x)}, boost_selections[3:6]))
        with col3:
            boosting_values += list(map(lambda x: {"key": x, "value" : st.number_input(f"{x}", value=boosts_values[x], min_value=0.01, on_change=utils.update_scoring_profile, args=search_settings, key=x)}, boost_selections[6:9]))


    select = fe_select

    # Get 2-col layout
    col1, col2 = st.columns([2,1])

    with col1:
        search = st.text_input("Search Query", "girl yellow cardigan")
            
    # Query testing
    query = search

    with col2:
        model_name = st.selectbox("Model", models, index=0)

    # Get embeddings results
    url = f"{base_url}/?query={query}&model_name={model_name}" 
    result = requests.get(url).json()


    # Filters
    st.sidebar.title("Filtering")
    if filters != None: # Read filter from environment if defined, use index filterable fields instead
        filter_selections = filters.replace(' ','').split(',')
    else:
        filter_selections = list(filter(lambda x: x in list(map(lambda x: x['name'], filterable)), selections))

    filter_checkboxes  = list(map(lambda x: {"key": x, "value" : st.sidebar.checkbox(f"Filter {x}"), "type" : types.get(x)}, filter_selections))
    
    # filter_checkboxes

    # Thresholds
    st.sidebar.title("Threshold definition")
    filter_thresholdes = list(map(lambda x: {"key": x, "value" : st.sidebar.number_input(f"{x}", value=85, min_value=0, max_value=100, step=1)}, filter_selections))

    # Select Top N
    st.sidebar.title("Top N Selection")
    selections_thresholdes = list(map(lambda x: {"key": x, "value" : st.sidebar.number_input(f"{x}", value=1, min_value=0, max_value=5, step=1)}, filter_selections))


    # Display embeddings result
    col1, col2 = st.columns([2,1])
    with col1: 
        df_result = pd.DataFrame(result)
        df_result
    
    with col2:
        if query != 'girl yellow cardigan': 
            gpt_3_query = utils.get_open_ai_suggested_query(query)
        else:
            gpt_3_query = " $search=girl yellow cardigan&$filter=color eq 'Yellow' and productTypeName eq 'Cardigan' and productGender eq 'Female'"
        gpt_3_query = gpt_3_query.strip().replace('$','\$')
        st.write(f"OpenAI GPT-3 suggested query (text-ada-01):\n\n{gpt_3_query}")
        # st.button('Update OpenAI GPT-3 suggested query',on_click=get_open_ai_suggested_query,args=query)


    # Get 2-col layout
    col1, col2 = st.columns(2)

    # Results
    with col1:
        st.header('Keyword based Search')
        st.write(f'Query: {query}')
        orig, counter = utils.send_query(search_settings, query, select= select, searchFields= fe_searchFields)
        st.write(f"Results count: {counter}")
        orig
    
    with col2:
        st.header('Search with Semantic Understanding')
        boost_data = utils.boost_terms(query, df_result, filter_checkboxes, filter_thresholdes, selections_thresholdes, boosting_checkboxes)
        st.write(f'Query: {boost_data["search"]}')
        boosted, counter = utils.send_query(search_settings,search_filters=boost_data, select=select, searchFields= fe_searchFields)
        st.write(f"Results count: {counter}")
        boosted

        st.write(f"Booster:  {' / '.join(list(map(lambda x: x, boost_data['booster'])))}")
        st.write(f"Filter: {boost_data['filters']}")

    st.header('Semantic Search')
    st.write(f'Query: {boost_data["search"]}')
    semantic, counter = utils.send_query(search_settings, search_filters=boost_data, select=select, semantic=True, searchFields= fe_searchFields)
    st.write(f"Results count: {counter}")

    semantic


except URLError as e:
    st.error(
        """
        **This demo requires internet access.**

        Connection error: %s
        """
        % e.reason
    )
