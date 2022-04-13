from azure.storage.blob import BlobClient
import os, json, logging
import utilities.azuresearch as acs
from pathlib import Path

# Get logging options:
logger = logging.getLogger(__name__)

def load_sample_data(path=os.getcwd(), search_settings={}):
    # Dowload sample product catalog from Azure Blob Storage
    blob_client = BlobClient.from_blob_url(os.getenv('sample_data_url'))
    data = blob_client.download_blob().readall()
    logging.info("Downloaded sample data")

    sample_data_path = os.path.join(path, 'data') 
    Path(sample_data_path).mkdir(parents=True, exist_ok=True)

    catalog_data_path = os.path.join(sample_data_path, 'catalog')
    Path(catalog_data_path).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(catalog_data_path, 'catalog.json'), 'wb') as download_file:
        download_file.write(data)

    article_data_path = os.path.join(sample_data_path, 'articles')
    Path(article_data_path).mkdir(parents=True, exist_ok=True)
    data = json.loads(data)
    for d in data:
        with open(os.path.join(article_data_path, f"{d['articleId']}.json"), 'w') as article_file:
            json.dump(d, article_file)

    # Push to Azure Cognitive Search
    acs.create_index(search_settings, os.path.join(os.path.join(sample_data_path, 'index') , 'index.json'))
    acs.push_data_to_search(search_settings=search_settings, path=os.path.join(sample_data_path, 'articles'))