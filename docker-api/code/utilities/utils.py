from sentence_transformers import SentenceTransformer, util
from ast import literal_eval
import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
import datetime, numpy as np, json, os, pandas as pd, logging

# Get logging options:
logger = logging.getLogger(__name__)

# Read JSON File
def read_json_file(file_path):
	with open(file_path, 'r') as f:
		return json.load(f)

# Read full prodct catalog
def extract_all_catalog(path):
    full_data = []
    # data_path = os.path.join(os.path.join(path, 'data') , 'articles')
    logging.info(f"data_path:{path}")
    for file in os.listdir(path):
        if file.endswith(".json"):
            file_path = os.path.join(path, file)
            full_data.append(read_json_file(file_path))
    return full_data

# Extract all import terms from catalog
def get_terms(path):

    term_file_path = os.path.join(path, 'embeddings' ,'terms.json')

    try:
        terms = read_json_file(term_file_path)
        logging.info(f'Terms loaded from path {term_file_path}')

    except Exception as e:
        logging.info(f"Creating new terms map from {path}")
    
        # Extract all items in the catalog
        full_data = extract_all_catalog(os.path.join(path,'data', 'articles'))
        # full_data = []
        # data_path = os.path.join(os.getcwd(), 'data')
        # for file in os.listdir(data_path):
        #     if file.endswith(".json"):
        #         file_path = os.path.join(path, file)
        #         full_data.append(read_json_file(file_path))
        logging.info(f"full_data: {len(full_data)}")

        # Get list of fields for embeddings
        fields = json.loads(os.getenv('fields'))

        # Extract field values
        terms = []
        for f in fields:
            f_terms = []
            if f['type'] == "Edm.ComplexType":
                f_terms = list(filter(None,set(map(lambda x: x.get(f.get('name')).get(f['subname']) if x.get(f.get('name')) else None, full_data))))
            elif f['type'] == "Collection(Edm.ComplexType)":
                for x in full_data:
                    for pq in x[f.get('name')]:
                        f_terms.append(pq[f['subname']])
                f_terms = list(filter(None,set(f_terms)))
            elif f['type'] == "Edm.String":
                f_terms = list(filter(None,set(map(lambda x: x.get(f.get('name')), full_data))))
            elif f['type'] == "Collection(Edm.String)":
                f_terms = set(filter(None, [item for sublist in list(map(lambda x: x.get(f.get('name')), full_data))  for item in sublist]))
            
            terms += list(filter(None,(map(lambda x : {"key": f.get('name'), "value": x}, list(f_terms)))))
            terms = sorted(terms, key= lambda i: (i['key'], i['value']), reverse=True)

        # Dump terms on file
        with open(term_file_path, 'w') as t_file:
            t_file.write(json.dumps(terms))

    return terms

# Computing Terms embedding
def compute_terms_embeddings(model,terms, path=os.getcwd()):
    if model['family'] == SentenceTransformer:
        start_time = datetime.datetime.now()
        terms_embedding = model['model'].encode(list(map(lambda x: x['value'], terms)))
        end_time = datetime.datetime.now()
        difference_in_ms = (end_time - start_time).total_seconds()*1000
        logging.info("terms", '(encoded in', difference_in_ms, 'ms)')
        np.save(os.path.join(path, 'embeddings' , model['name']), terms_embedding)
        return terms_embedding

    elif model['family'] == 'GPT-3':
        df_terms = pd.DataFrame(terms)        
        start_time = datetime.datetime.now()
        df_terms['gpt_3_search'] = df_terms.value.apply(lambda x: get_embedding(x, engine= model['name']))
        end_time = datetime.datetime.now()
        difference_in_ms = (end_time - start_time).total_seconds()*1000
        logging.info("terms", '(encoded in', difference_in_ms, 'ms)')
        df_terms.to_csv(os.path.join(path, 'embeddings' , f"{model['name']}.csv"))
        return df_terms
  
# Take a query and find the similarity to a set of sentences or terms
def process_query(query, terms_embedding, model, terms):
    if model['family'] == SentenceTransformer:
        start_time = datetime.datetime.now()
        query_embedding = model['model'].encode(query)
        end_time = datetime.datetime.now()
        difference_in_ms = (end_time - start_time).total_seconds()*1000
        logging.info(query, '(encoded in', difference_in_ms, 'ms)')

        if model['name'] in ['msmarco-distilbert-dot-v5']:
            logging.info(f'Using dot_score for {model["name"]}')
            scores = util.dot_score(query_embedding, terms_embedding).numpy()[0]
        else:
            logging.info(f'Using cos_similarity for {model["name"]}')
            scores = util.cos_sim(query_embedding, terms_embedding).numpy()[0]

        # scores = util.cos_sim(query_embedding, terms_embedding).numpy()[0]
        
        terms_score = []
        counter = 0
        for score in scores:
            terms_score.append(
                {
                    "term": terms[counter]['value'],
                    "key" : terms[counter]['key'],
                    "score" : str(score),
                    "query" : query,
                    "model_name" : model['name']
                }
            )
            counter+=1

        return sorted(terms_score, key = lambda i: i['score'],reverse=True)

    else:

        start_time = datetime.datetime.now()
        query_embedding = get_embedding(query, engine=model['name'])
        end_time = datetime.datetime.now()
        difference_in_ms = (end_time - start_time).total_seconds()*1000
        logging.info(query, '(encoded in', difference_in_ms, 'ms)')
        
        terms_embedding['score'] = terms_embedding.gpt_3_search.apply(lambda x: cosine_similarity(x, query_embedding))
        
        res = terms_embedding.sort_values('score', ascending=False).head(5)

        res.drop(['gpt_3_search'], axis=1, inplace=True)
        res['query'] = query
        res['model_name'] = model['name']
        
        return res.to_dict('records')

# Define model structure
def get_model(family, name):
    return {
            "family": family,
            "name" : name,
            "model" : family(name) if family == SentenceTransformer else name
    }

# Load or compute embeddings
def get_model_embeddings(model, terms, path=os.getcwd()):
    if model['family'] == SentenceTransformer:
        try:
            terms_embedding = np.load(os.path.join(path,"embeddings", f"{model['name']}.npy"))
            logging.info(f"Embeddings loaded for model {model['name']}")
        except Exception as e:
            logging.info(e)
            logging.info(f"Creating new embeddings with model {model['name']}")
            terms_embedding = compute_terms_embeddings(model,terms)
        return terms_embedding

    elif model['family'] == "GPT-3":
        try:
            terms_embedding = pd.read_csv(os.path.join(path, "embeddings", f"{model['name']}.csv"), index_col=0)
            logging.info(f"Embeddings loaded for model {model['name']}")
            terms_embedding.gpt_3_search = terms_embedding.gpt_3_search.apply(literal_eval)
        except Exception as e:
            logging.info(f"Creating new embeddings with model {model['name']}")
            terms_embedding = compute_terms_embeddings(model,terms)
        return terms_embedding

# Load all models
def load_models(sentence_transformers_models, gpt_3_models, path= os.getcwd(), openai_api_key= os.environ.get('OPENAI_API_KEY')): 
    terms = get_terms(path) 

    openai.api_key = openai_api_key

    all_models = {}
    if sentence_transformers_models != '':
        for m in os.environ['SentenceTransformer'].replace(' ','').split(','):
            mod = get_model(SentenceTransformer, m)
            t_emb = get_model_embeddings(mod, terms)
            all_models[mod['name']] = {
                "model" : mod,
                "terms_embedding" : t_emb
            }

    if gpt_3_models != '':
        for m in os.environ['GPT_3'].replace(' ','').split(','):
            mod = get_model("GPT-3", m)
            t_emb = get_model_embeddings(mod, terms)
            all_models[mod['name']] = {
                "model" : mod,
                "terms_embedding" : t_emb
            }
    
    return all_models, terms

