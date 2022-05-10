# Azure Search - Query Classification

Search experiences are all around us, empowering us to quickly find the documents, websites, products and answers that we're looking for. 

For years, search engines have employed complex machine learning techniques to more deeply understand what users are searching for and to help them find it. 
These techniques enable search engines to semantically understand a user's query, to know that Debussy was a classical musician, that a dog is a pet, and that Python and JavaScript are programming languages. 

In catalog search, semantically understanding the intent and extracting the entities in the query is crucial to provide useful results. Whenever the users type "blue girl cardigan", they expect the search engine to correctly identify the color as well as the specific product type and their intent to get back only female products.

Though these techniques help us find what we're looking for, they have not been available to enterprises who want to build their own semantic search capabilities.

[Azure Cognitive Search](https://docs.microsoft.com/azure/search/search-what-is-azure-search) aims to provide [semantic understanding](https://docs.microsoft.com/azure/search/semantic-search-overview) capabilities to search, so that any enterprise can build much more natural search experiences.

## About this repo

This sample demonstrates how we can use word embeddings from Large Language Models (LLMs) with Azure Cognitive Search to create search experiences that understand the relationships between the entities in a query and the products in a catalog.

The project combines [OpenAI embedding models](https://beta.openai.com/docs/api-reference/embeddings) and Azure Cognitive Search to enhance search relevancy by adding a semantic understanding layer in query composition. Whenever a user searches for something, it is crucial to understand his/her intent to provide a tailored result set, considering both the entities in the query and the semantic similarity to the available products. 

The solution creates an embedding representation of a product catalog to improve search relevancy by applying an implicit semantic classification step whenever a user submits a new query.
The code extracts product data from a search index, computes and stores the embeddings based on OpenAI model (ada, babbage or curie) and applies the same embedding technique to every new unseen query coming to the engine. The query embeddings are evaluated against the embeddings matrix to determine the semantic similarity score and return possible filters criteria, boosting criteria or query expansion with confidence thresholds. 

This project also converts natural language into Lucene queries using a few-shot approach and OpenAI text generation models as an alternative for query composition.

The code is split into two different logical components to facilitate re-use and an easy integration in any application layer of your choice:
-   docker-api: core component computing the embedding matrix for the product catalog and exposing an API for query embedding and semantic scoring
-   docker-web: a sample experimentation UI to visualize embeddings results and threshold to test your dataset and defining the right filtering, boosting and query expansion logic 

Both components are dockerized for easy deployment on multiple platforms and integration with existing applications. 

## Statement of Purpose
The purpose of this repository is to grow the understanding of using Large Language Models in Azure Cognitive Search by providing an example of implementation and references to support the [Microsoft Build conference in 2022](https://mybuild.microsoft.com/). It is not intended to be a released product. Therefore, this repository is not for discussing OpenAI API, Azure Cognitive Search or requesting new features.

## How semantic search changes the results set
Let's see how semantic understanding changes the results set with a sample query.

The "girl yellow cardigan" query is analyzed and three entities are extracted as the most probable match, also with their attribute key.
So, "yellow" is classified as color, "cardigan" as a product type and "girl" clearly indicates the need for "female" as product gender.
![semantic-understanding](/doc-images/semantic-understanding.png)

Using this information, a filter on the product gender is applied to return just products classified as "Female" and a boost is pushing "yellow" products on top of the results set.
You can easily compare the results in the following image.
![semantic-understanding](/doc-images/keyword-vs-semantic.png)


## Requirements

- [Azure Cognitive Search](https://docs.microsoft.com/en-us/azure/search/search-what-is-azure-search#how-to-get-started) with [Standard SKU and Semantic Search](https://docs.microsoft.com/en-us/azure/search/semantic-search-overview#enable-semantic-search)
- [Python 3.8+](https://wiki.python.org/moin/BeginnersGuide/Download)
- [Docker](https://docs.docker.com/get-started/)
- Open AI API Key to make API calls 

## Running the App Locally (without Docker)
1. `git clone` the repo: `git clone https://github.com/microsoft/azure-search-query-classification` and open the project folder
2. Create a `.env` file in the root directory of the project, copying the contents of the `.env.example` file [See Configure the .env file section](#configure-the-env-file) 
3. Gather the projects' dependencies for the backend component
    - Windows users: Run `pip install -r docker-api\code\requirements.txt` 
    - MacOs users: Run `pip install -r docker-api/code/requirements.txt`
4. Gather the projects' dependencies for the frontend component
    - Windows users: Run `pip install -r docker-web\code\requirements.txt`
    - MacOs users: Run `pip install -r docker-web/code/requirements.txt` 
5. Run `python local-run.py` to serve the backend and launch the web application.
NOTE for MacOs users: by default no alias for python is defined. In this case, please run `python3 local-run.py`

## Running the App Locally (with Docker)
1. [Check whether Docker is running](https://docs.docker.com/config/daemon/#check-whether-docker-is-running)
2. `git clone` the repo: `git clone https://github.com/microsoft/azure-search-query-classification` and open the project folder
2. Create a `.env` file in the root directory of the project, copying the contents of the `.env.example` file [See Configure the .env file section](#configure-the-env-file)
3. Create the server docker image
    -   Windows users: Run `docker build docker-api\. -t YOUR_REGISTRY/YOUR_REPO/YOUR_API:TAG`
    -   MacOs users: Run `docker build docker-api/. -t YOUR_REGISTRY/YOUR_REPO/YOUR_API:TAG`
4. Create the client docker image
    -   Windows users: Run `docker build docker-web\. -t YOUR_REGISTRY/YOUR_REPO/YOUR_WEB:TAG` 
    -   MacOs users: Run `docker build docker-web/. -t YOUR_REGISTRY/YOUR_REPO/YOUR_WEB:TAG` 
5. Modify the `docker-compose.yml` to point to your images tags as defined in step 3 and step 4
6. Run `docker compose up` to serve the backend and launch the web application.

## Configure the .env file

Please use your own settings in the fields marked as "TO UPDATE" in the Note column in the following table.

<br>

| App Setting         | Value                           | Note                                                             |
|---------------------|---------------------------------|------------------------------------------------------------------|  
| search_service |YOUR_AZURE_COGNITIVE_SEARCH_SERVICE | TO UPDATE [Azure Cognitive Search service name](https://docs.microsoft.com/en-us/azure/search/search-create-service-portal#name-the-service) e.g. https://XXX.search.windows.net use just XXX.|
| index_name | YOUR_AZURE_COGNITIVE_SEARCH_INDEX | TO UPDATE A new index that will be created by the code in your Azure Cognitive Search resource |
| api_key | YOUR_AZURE_COGNITIVE_SEARCH_API_KEY | TO UPDATE [Azure Cognitive Search Admin Key](https://docs.microsoft.com/en-us/azure/search/search-create-service-portal#get-a-key-and-url-endpoint) |
| api_version| 2021-04-30-Preview | [Azure Cognitive Search API Version](https://docs.microsoft.com/en-us/azure/search/search-api-versions) |
| LoadSampleData | true | Load sample data in Azure Cognitive Search index |
| sample_data_url | | Link to download sample data if LoadSampleData is true |
||||
||||
| SentenceTransformer | msmarco-distilbert-dot-v5, all-mpnet-base-v2, nq-distilbert-base-v1, all-MiniLM-L6-v2| List of all the models for compute the embeddings. You can add any [Sentence Transformers](https://huggingface.co/sentence-transformers) |
| GPT_3 | text-search-curie-query-001, text-search-babbage-query-001, text-search-ada-query-001 | List of all the models for compute the embeddings. You can add any [GPT-3 embedding model](https://beta.openai.com/docs/guides/embeddings) |
| OPENAI_API_KEY | YOUR_OPENAI_API_KEY | TO UPDATE [OpenAI GPT-3 Key](https://beta.openai.com/docs/api-reference/authentication) |
||||
||||
| fields | <pre> [<br>    {<br>      "name": "name",<br>      "type": "Edm.String"<br>    },<br>    {<br>      "name": "quality",<br>      "type": "Collection(Edm.String)"<br>    },<br>    {<br>      "name": "style",<br>      "type": "Collection(Edm.String)"<br>    },<br>    {<br>      "name": "gender",<br>      "type": "Edm.String"<br>    },<br>    {<br>      "name": "colors",<br>      "type": "Collection(Edm.String)"<br>    },<br>    {<br>      "name": "type",<br>      "type": "Edm.String"<br>    }<br> ] </pre>| JSON version of all the fileds to be used for computing embeddings |
||||
||||
| select | articleId,type,name,description,quality,style,gender,colors | List of all Azure Cognitive Search index fields to visualize in the UI results table |
| searchFields | articleId,type,name,description,quality,style,gender,colors | List of all Azure Cognitive Search fields to search in |
| boost | type,name,quality,style,gender,colors | List of all Azure Cognivite Search fields to be used for attribute boosting in the UI |
| filters | type,name,quality,style,gender,colors | List of all Azure Cognivite Search fields to be used for attribute filtering in the UI |
||||
||||
| prod_url | http://api:80 or http://localhost:8000 |URL for the Server side component (docker-api microservices) as defined in the [docker compose file](./docker-compose.yml) When executing locally without Docker, use http://localhost:8000 instead|
| gpt3_prompt | girl yellow cardian -> $search=girl yellow cardigan&$filter=color eq 'Yellow' and productTypeName eq 'Cardigan' and productGender eq 'Female'\nblu man t-shirt -> $search=blu man t-shirt&$filter=color eq 'Blue' and productTypeName eq 'T-shirt' and productGender eq 'Male'\nblack hoodie ->  $search=black hoodie&$filter=color eq 'Black' and productTypeName eq 'Hoodie'\ncotton black pant -> $search=cotton black pant&$filter=color eq 'black' and productTypeName eq 'Black' and productQuality eq 'cotton'\nlight blue cotton polo shirt -> $search=light blue cotton polo shirt&$filter=color eq 'Light Blue' and productQuality eq 'Cotton' and productTypeName eq 'Polo Shirt'\ngreen cashmere polo shirt -> $search=green cashmere polo shirt&$filter=color eq 'Green' and productQuality eq 'Cashmere' and productTypeName eq 'Polo Shirt'\n | [OpenAI Prompt for query generation](https://beta.openai.com/docs/introduction/key-concepts) |

## Using the App

Example queries:
-    girl yellow cardigan
-    women white belted coat


## How to use embeddings
The core of the repo is using the _encode_ function from __sentence_transformers__ library and _get_embeddings_ from __openai__ library to compute the embedding representations of the product attributes available in a sample product catalog.
```python 
# docker-api\code\utilities\utils.py
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
```

Whenever a user submits a query, the same libraries are used to compute the embeddings for the whole sentence and the single words in it and semantically rank this terms list against all available product attributes.

```python
# docker-api\code\utilities\utils.py
def process_query(query, terms_embedding, model, terms):
    if model['family'] == SentenceTransformer:
        start_time = datetime.datetime.now()
        query_embedding = model['model'].encode(query)
        end_time = datetime.datetime.now()
        difference_in_ms = (end_time - start_time).total_seconds()*1000
        logging.info(query, '(encoded in', difference_in_ms, 'ms)')

        logging.info(f'Using cos_similarity for {model["name"]}')
        scores = util.cos_sim(query_embedding, terms_embedding).numpy()[0]

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
```

## Build a Docker image
### Server
1. `docker build docker-api\. -t YOUR_REGISTRY/YOUR_REPO/YOUR_API:TAG`
2. `docker run -p 80:80 --env-file .env -t YOUR_REGISTRY/YOUR_REPO/YOUR_API:TAG`

### Client
1. `docker build docker-web\. -t YOUR_REGISTRY/YOUR_REPO/YOUR_WEB:TAG`
2. `docker run -p 80:80 --env-file .env -t YOUR_REGISTRY/YOUR_REPO/YOUR_WEB:TAG`


## Debugging
To debug the web application, you can [debug with VSCode debugger](https://code.visualstudio.com/Docs/editor/debugging).

### Server
[FastAPI Debugging tool](https://fastapi.tiangolo.com/tutorial/debugging/)

### Client
[Streamlit Debugging](https://awesome-streamlit.readthedocs.io/en/latest/vscode.html)

## Undestand the Code
### Server (docker-api)
-   `api.py` is the main entry point for the app, it uses FastAPI to serve RESTful APIs.
-   `utilities` is the module with utilities to extract product catalog data, compute embeddings and the semantic similarity score for a new query

### Client (docker-web)
-   `ui.py` is the entry to bootstrap the Streamlit web application
-   `utilities` is the module with utilities for interact with the search index and the server-side



## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
