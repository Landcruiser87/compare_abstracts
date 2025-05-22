import contextlib
import datetime
import json
import re
import spacy
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine as scipy_cos
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cos
from sentence_transformers import SentenceTransformer, util as t_utils

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
        if abstract != None:
            re_txt = re.sub('[\W_]+', ' ', abstract)
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
    try:
        if model_name == "Marco": #Polooooooo.  
            model = SentenceTransformer("msmarco-MiniLM-L6-v3")  #80MB
        elif model_name == "Specter":
            model = SentenceTransformer("allenai-specter")
            # trained on finding similar papers.  
            # could have an extra option pop up when its selected to find a
            # similar paper to what is selected. 
        return model
        
    except Exception as e:
        raise ValueError(f"You need to install sentence-transformers for model {model_name}")

