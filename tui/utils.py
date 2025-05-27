import contextlib
import datetime
import urllib
import json
import re
import os
import spacy
import numpy as np
import pandas as pd
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine as scipy_cos
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cos
from sentence_transformers import SentenceTransformer
from support import logger


#FUNCTION get time
def get_c_time():
    """Function for getting current time

    Returns:
        current_t_s (str): String of current time
    """
    current_t_s = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    return current_t_s

#FUNCTION Clean String vals
def clean_string_values(obj: dict|list|str) -> dict|list|str:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                value = value.replace("\\r\\n", "")
                with contextlib.suppress(json.JSONDecodeError):
                    value = json.loads(value)
            cleaned_value = clean_string_values(value)
            obj[key] = cleaned_value
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            cleaned_value = clean_string_values(value)
            obj[i] = cleaned_value
    elif isinstance(obj, str):
        obj = obj.replace("\\r\\n", "").replace('\\"', '"')

    return obj

def clean_text(srch_text:str, srch_field, node)-> list:
    #Pull out the fields into a list
    data_fields = [x.data.get(srch_field) for x in node.children]
    paper_names = [x.label.plain.strip("{}").strip() for x in node.children]
    with open("./data/stopwords.txt", "r") as f:
        stopwords_list = f.read()
    # stopwords_list = requests.get("https://gist.githubusercontent.com/rg089/35e00abf8941d72d419224cfd5b5925d/raw/12d899b70156fd0041fa9778d657330b024b959c/stopwords.txt").text
    stopwords = set(stopwords_list.splitlines())
    #Add the search term to the list at the zero index
    data_fields.insert(0, srch_text)
    paper_names.insert(0, "papernames")

    #Remove and clean stopwords
    for idx, abstract in enumerate(data_fields):
        if (abstract != None) & (isinstance(abstract, str)):
            re_txt = re.sub(r'[\W_]+', ' ', abstract)
            l_txt = re_txt.lower().split()
            s_txt = [word for word in l_txt if word not in stopwords and not word.isnumeric()]
            data_fields[idx] = " ".join(s_txt)
        else:
            data_fields[idx] = ""
    return data_fields, paper_names

def tfidf(data_fields:list, paper_names:list):
    #L1 normlization
    base_params = {
        "binary":False, 
        "norm":"l1",
        "use_idf":False, 
        "smooth_idf":False,
        "lowercase":True, 
        "stop_words":"english",
        "min_df":1, 
        "max_df":1.0, 
        "max_features":None,  
        "ngram_range":(1, 1)
    }
    model = TfidfVectorizer(**base_params)
    tsfrm = model.fit_transform(data_fields)
    feats = model.get_feature_names_out()
    tsfrm_df = pd.DataFrame(
        tsfrm.toarray(),
        columns=feats,
        index=paper_names
	)
    return tsfrm_df, paper_names


def cosine_similarity(tsfrm, ts_type:str):
	"""Function that allows you to use either sklearns, or scipy's cosine similarity
	Inputs are already in a sparse array format.  Scipy uses np.arrays, but the code 
	below will handle that. 

	Args:
		tsfrm (sparse array): Sparse Matrix of Documents
		ts_type (str): Version of Cosine Similarity you want

	Raises:
		ValueError: If you don't specify "scipy" or "sklearn", it throws an error.

	Returns:
		float: Cosine similarity
	"""	
    
	if ts_type == "sklearn":
		sims = sklearn_cos(tsfrm[0], tsfrm)
		return sims.flatten()
	
	elif ts_type == "scipy":
		sims = []
		X = tsfrm.iloc[0]
		for row in range(tsfrm.shape[0]):
			y = tsfrm.iloc[row]
			sims.append(1 - scipy_cos(X, y))
		return sims
	else:
		raise ValueError (f"{ts_type} not an available cosine transform. Check spelling for scipy or sklearn")

def embedding_cos_sim(query:str, compare:str):
    """Manual cosine similarity calculation

    Args:
        query (str): query text
        compare (str): text to compare

    Returns:
        _type_: cosine similarity (-1 to 1)
    """    
    return np.dot(query, compare) / (np.linalg.norm(query) * np.linalg.norm(compare))

def word2vec():
    try:
        model_name = "en_core_web_md"
        nlp = spacy.load(model_name)
        return nlp
    except Exception as e:
        raise ValueError(f"No Soup for you! Download the model by running python -m spacy download {model_name}")


def sbert(model_name:str):
    #TODO - UPDATE THIS SO ITS NOT DINGUS MATERIAL
        #ie the folder creation and download of the models
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # device = "cpu"
        #I'd suggest using the cached version of each model.  
        #Trained on a bunch of bing queries
        if model_name == "Marco": #Polooooooo.
            model_path = "./data/models/marco/"
            if os.path.exists(model_path):
                model = SentenceTransformer(model_path, device = device)
                logger.info("Model loaded locally")
            else:
                
                model = SentenceTransformer("msmarco-MiniLM-L6-v3", device = device)  #80MB
                model.save_pretrained("./data/models/marco")
                logger.info("Model loaded and saved dynamically")

        # trained on finding similar papers.  Works better with abstracts
        elif model_name == "Specter":
            model_path = "./data/models/specter"
            if os.path.exists(model_path):
                model = SentenceTransformer(model_path, device = device)
                logger.info("Model loaded locally")                
            else:
                model = SentenceTransformer("allenai-specter", device = device) #425 MB
                model.save_pretrained("./data/models/specter")
                logger.info("Model loaded and saved dynamically")

        return model, device
        
    except Exception as e:
        raise ValueError(f"You need to install sentence-transformers for model {model_name}")

def search_arxiv():
    # main url - http://export.arxiv.org/api/query
    # NOTE - Can only make a request every 3 seconds. 
        # Due to speed limitations in our implementation of the API, the maximum
        # number of results returned from a single call (max_results) is limited to
        # 30000 in slices of at most 2000 at a time,
    #Import search params, 
    #Export search results in JSON format. 
        #Means I'll need an exporting process too.
    subj_params = {
        "prefix": "explanation",
        "ti": "Title",
        "au": "Author",
        "abs": "Abstract",
        "co": "Comment",
        "jr": "Journal Reference",
        "cat": "Subject Category",
        "rn": "Report Number",
        "id": "Id (use id_list instead)",
        "all": "All of the above"
    }


    # Couple of different ways we can go here.  
    #1.  Use the official Arxiv wrapper built by Lukas Scwab.  Looks like he's still updating it and its fairly useful.  
    #2.  Build my own.  Much harder route, but we'll see if I care about one more dependency.