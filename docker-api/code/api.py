from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
import utilities.utils as utils
from utilities.load_sample_data import load_sample_data
import os
import logging

app = FastAPI()

# from dotenv import load_dotenv
# load_dotenv(r'C:\repos\product-embeddings\.env')

# Configure logging options:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

# Push sample data in Azure Cognitive Search
if os.environ.get('LoadSampleData'):
    search_settings = {}
    search_settings['search_service']   = os.getenv('search_service')
    search_settings['index_name']       = os.getenv('index_name')
    search_settings['api_version']      = os.getenv('api_version')  
    search_settings['api_key']          = os.getenv('api_key')      
    load_sample_data(search_settings=search_settings)


# Loads all models specified in the Environmental settings
all_models, terms = utils.load_models(
        sentence_transformers_models = os.environ.get('SentenceTransformer', ''),
        gpt_3_models = os.environ.get('GPT_3',''),
        path= os.getcwd(),
        openai_api_key= os.environ.get('OPENAI_API_KEY')
    )

# App serving
@app.get("/")
async def root(query: str, model_name: str):

    results = []

    query_terms = [query]
    query_terms += query.split(' ')

    results += list(map(lambda x: utils.process_query(x, all_models[model_name]['terms_embedding'], all_models[model_name]['model'], terms)[0:5], query_terms))
    results = [item for sublist in results for item in sublist]

    return results

@app.get("/ready")
async def ready():
    return "API ready to serve requests"
