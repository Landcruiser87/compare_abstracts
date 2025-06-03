import contextlib
import datetime
import requests
import json
import re
from os import path
import spacy
import numpy as np
import pandas as pd
import torch
import time
from dataclasses import dataclass, asdict, fields
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup
from scipy.spatial.distance import cosine as scipy_cos
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cos
from sentence_transformers import SentenceTransformer
from support import logger, NumpyArrayEncoder

@dataclass
class Paper:
    title   : str  | None = None
    authors : list | None = None
    keywords: list | None = None
    category: list | None = None
    abstract: str = ""
    url     : str = ""
    pdf     : str = ""
    github_url     : str = ""  
    supplemental   : str = ""  #general comments
    date_published : str = ""  # mm-dd-yyyy
    conference_info: str = ""  # e.g. arxiv

class ArxivSearch(object):
    def __init__(self, variables:dict):
        self.params: dict = variables
        self.results: list = []

    def is_a_date(self, datetext:str):
        try:
            datetime.datetime.strptime(datetext, "%Y-%m-%d")
            return True
        except Exception as e:
            logger.warning(f"date extraction error.  Check inputs\n{e}")
            return False
        
    def date_format(self):
        self.params["dates"] = self.params["dates"].lower().split()
        self.params["dates"] = "_".join(self.params["dates"])
        self.params["submitted_date"] = datetime.datetime.today().date()
        self.params["submitted_date"] = self.params["submitted_date"].strftime("%Y-%m-%d")

        #Don't need logic for all_dates
        #works
        if self.params["dates"] == "specific_year":
            start = self.params["year"]
            if len(start) == 4 and start.isdigit():
                return True
            else:
                return False
        #works
        elif self.params["dates"] == "past_12_months":
            self.params["start_date"] = datetime.datetime.today().date() - datetime.timedelta(days=365)
            self.params["start_date"] = self.params["start_date"].strftime("%Y-%m-%d")
            self.params["end_date"] = self.params["submitted_date"]
            self.params["dates"] = "past_12"
            return True
        #doesn't work
        elif self.params["dates"] == "date_range":
            start = self.params["start_date"]
            end = self.params["end_date"]
            for val in [start, end]:
                if not self.is_a_date(val):
                    logger.warning("Error in date formatting, please check inputs")
                    return False
            return True
        #works
        elif self.params["dates"] == "all_dates":
            #NOTE come back and check the date format for here. 
            return True
    
    def parse_feed(self, results:list) -> dict:
        paper_dict = {}
        for idx, result in enumerate(results):
            paper = Paper()
            #Get the URL
            url = result.find("p", {"class":"list-title is-inline-block"})
            paper.url = url.select("a")[0].get('href')
            #Grab title
            paper.title = result.find("p", attrs={"class": lambda e: e.startswith("title")}).text.strip()
            paper.id = str(idx) + "_" + paper.title
            #Grab authors
            authors = result.find("p", {"class":"authors"})
            if authors != None:
                paper.authors = {str(idx) + "_" + x.text:x.text for idx, x in enumerate(authors.find_all("a"))}
            #Abstract
            paper.abstract = result.find("span", attrs={"class":"abstract-full"}).text.strip()[:-15]
            categories = result.find("div", attrs={"class":"tags is-inline-block"})
            if categories != None:
                paper.category = categories.text.split()

            comments = result.find("p", attrs={"class": lambda e: e.startswith("comments")})
            if comments != None:
                comment_= comments.find("span", attrs={"class":"has-text-grey-dark mathjax"})
                if comment_ != None:
                    paper.supplemental = comment_.text

            published = result.find("p", attrs={"class":"is-size-7"})
            if published != None:
                temp = published.find("span", attrs={"class": lambda e: e.startswith("has-text-black-bis")})
                if temp.text == "Submitted":
                    paper.date_published = datetime.datetime.strptime(temp.next_sibling.strip().strip(";"), '%d %B, %Y')

            if "github" in paper.abstract:
                #This regex will pull out a github.io or github.com link
                pattern = r"((?:https?://)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)?github\.(?:com|io)(?:/[a-zA-Z0-9\._-]+)*)"
                possiblematch = re.findall(pattern, paper.abstract)
                if possiblematch:
                    paper.github_url = possiblematch[0]
            paper.conference_info = "https://arxiv.org"
            paper_dict[paper.id] = {field.name: getattr(paper, field.name) for field in fields(paper)}# asdict(paper). asdict not saving the authors keys
            del paper

        return paper_dict
          
    def classification_format(self):
        main_cat = self.params["subject"].lower()
        if " " in main_cat:
            main_cat = "_".join(main_cat.split())
        self.params["classification"] = f"classification-{main_cat}"
        search_cat = self.params["categories"]
        
        try:
            if len(search_cat) > 1:
                self.params["categories"] = "+OR+".join(search_cat)
                self.params["add_cat"] = True
            #BUG - may not need last elif
                #I think that's just for  the physics archives which for some
                #reason they hardcode into the request. 
            # elif len(search_cat) == 0:
            #     self.params["categories"] = "all"
            return True
        
        except Exception as e:
            logger.warning(f"Error in classification formatting\n{e}")
            return False
        
    def request_papers(self) -> dict:
        chrome_version = np.random.randint(120, 135)
        baseurl = "https://arxiv.org/search/advanced"
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=0, i',
            'referer': baseurl,
            'sec-ch-ua': f'"Not)A;Brand";v="99", "Google Chrome";v={chrome_version}, "Chromium";v={chrome_version}',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': f'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36',
        }

        #Input validation checks
        formatted = self.date_format()
        classy = self.classification_format()
        if not formatted or not classy:
            return None, "Error in formatting classification or date"

        #NOTE - Might need to update this with separate terms.
        #Eventually update this query to operate on multiple separate terms
        parameters = {
            'advanced': '',                        
            'terms-0-operator': 'AND',              
            'terms-0-term': self.params["query"],
            'terms-0-field': self.params["field"],
            self.params["classification"]:'y',
            'classification-include_cross_list': 'include',
            'date-filter_by': self.params["dates"],
            'date-year': self.params["year"],
            'date-from_date': self.params["start_date"],
            'date-to_date': self.params["end_date"],
            'date-date_type': "submitted_date_first", 
            'abstracts': 'show',
            'size': self.params["limit"],
            'order':'-submitted_date',
        }
        if self.params["add_cat"]:
            parameters[f'{self.params["classification"]}' + "_archives"]  = self.params["categories"]

        try:
            response = requests.get(baseurl, headers=headers, params=parameters)
            
        except Exception as e:
            logger.warning(f"A general request error occured.  Check URL\n{e}")

        if response.status_code != 200:
            logger.warning(f'Status code: {response.status_code}')
            logger.warning(f'Reason: {response.reason}')
            return None, f"Status Code {response.status_code} Reason: {response.reason}"
        
        time.sleep(2) #Be nice to the servers
        bs4ob = BeautifulSoup(response.content, "lxml")
        results = bs4ob.find_all("li", {"class":"arxiv-result"})
        if results:
            logger.info(f'{len(results)} papers returned from arxiv searching {self.params["query"]}')
            new_papers = self.parse_feed(results)
            return new_papers, None

        else:
            err_message =f"No papers returned for search ({self.params['query']}) in category {self.params['subject']}"
            logger.warning(err_message)
            return None, err_message

        # NOTE - Can only make a request every 3 seconds. 
        # NOTE - Don't feel like dealing with pagination so.  200 is the max request limit!

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
        #Trained on a bunch of bing queries
        if model_name == "Marco": #Polooooooo.
            model_path = "./data/models/marco/"
            if path.exists(model_path):
                model = SentenceTransformer(model_path, device = device)
                logger.info("Model loaded locally")
            else:
                model = SentenceTransformer("msmarco-MiniLM-L6-v3", device = device)  #80MB
                model.save_pretrained("./data/models/marco")
                logger.info("Model loaded and saved dynamically")

        # trained on finding similar papers.  Works better with abstracts but takes a really long time
        elif model_name == "Specter":
            model_path = "./data/models/specter"
            if path.exists(model_path):
                model = SentenceTransformer(model_path, device = device)
                logger.info("Model loaded locally")                
            else:
                model = SentenceTransformer("allenai-specter", device = device) #425 MB
                model.save_pretrained("./data/models/specter")
                logger.info("Model loaded and saved dynamically")

        return model, device
        
    except Exception as e:
        raise ValueError(f"You need to install sentence-transformers for model {model_name}")
