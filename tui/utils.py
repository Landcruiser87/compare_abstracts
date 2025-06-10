import contextlib
import datetime
import requests
import json
import re
from os import path, mkdir
import spacy
import numpy as np
import pandas as pd
import torch
import time
from urllib.parse import urlencode, quote
from dataclasses import dataclass, asdict, fields
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup
from scipy.spatial.distance import cosine as scipy_cos
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cos
from sentence_transformers import SentenceTransformer
from support import logger


################################# Classes #################################
@dataclass
class Paper:
    title   : str  | None = None
    authors : list | None = None
    keywords: list | None = None
    category: list | None = None
    abstract: str = ""
    url     : str = ""
    pdf     : str = ""
    doi     : str = ""            
    github_url     : str = ""
    supplemental   : str = ""  #general comments
    date_published : str = ""  # mm-dd-yyyy
    conference_info: str = ""  # e.g. arxiv

class ArxivSearch(object):
    def __init__(self, variables:dict):
        self.params: dict = variables
        self.results: list = []

    def date_format(self):
        self.params["dates"] = self.params["dates"].lower().split()
        self.params["dates"] = "_".join(self.params["dates"])
        self.params["submitted_date"] = datetime.datetime.today().date()
        self.params["submitted_date"] = self.params["submitted_date"].strftime("%Y-%m-%d")

        if self.params["dates"] == "specific_year":
            start = self.params["year"]
            if len(start) == 4 and start.isdigit():
                return True
            else:
                return False
        elif self.params["dates"] == "past_12_months":
            self.params["start_date"] = datetime.datetime.today().date() - datetime.timedelta(days=365)
            self.params["start_date"] = self.params["start_date"].strftime("%Y-%m-%d")
            self.params["end_date"] = self.params["submitted_date"]
            self.params["dates"] = "past_12"
            return True
        elif self.params["dates"] == "date_range":
            start = self.params["start_date"]
            end = self.params["end_date"]
            for val in [start, end]:
                if not is_a_date(val):
                    logger.warning("Error in date formatting, please check inputs")
                    return False
            return True
        elif self.params["dates"] == "all_dates":
            #NOTE come back and check the date format for here. 
            return True
    
    def parse_feed(self, results:list) -> dict:
        paper_dict = {"search_params":self.params}
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
        
        time.sleep(3) #Be nice to the servers
        bs4ob = BeautifulSoup(response.content, "lxml")
        results = bs4ob.find_all("li", {"class":"arxiv-result"})
        if results:
            logger.info(f'{len(results)} papers returned from arxiv searching {self.params["query"]}')
            new_papers = self.parse_feed(results)
            return new_papers, None

        else:
            message =f"No papers returned for search ({self.params['query']}) in category {self.params['subject']}"
            logger.warning(message)
            return None, message

        # NOTE - Can only make a request every 3 seconds. 
        # NOTE - Don't feel like dealing with pagination so.  200 is the max request limit!

class xRxivBase(object):
    def __init__(
        self,
        server: str,
        launchdt: str,
        params: dict,
        base_url: str = "https://www.biorxiv.org",
        
    ):
        self.server  : str = server
        self.launchdt = launchdt
        self.params = params
        self.base_url = base_url
        self.results : list = []
        self.cursor : int = 0

    def _date_format(self):
        self.params["dates"] = self.params["dates"].lower().split()
        self.params["dates"] = "_".join(self.params["dates"])
        self.params["submitted_date"] = datetime.datetime.today().date()
        self.params["submitted_date"] = self.params["submitted_date"].strftime("%Y-%m-%d")

        if self.params["dates"] == "specific_year":
            start = self.params["year"]
            if len(start) == 4 and start.isdigit():
                self.params["start_date"] = f"{start}-01-01"
                if self.params["submitted_date"][:4] == start:
                    self.params["end_date"] = self.params["submitted_date"]
                else:
                    self.params["end_date"] = f"{self.params["year"]}-12-31"
                return True
            else:
                return False
        elif self.params["dates"] == "past_12_months":
            self.params["start_date"] = datetime.datetime.today().date() - datetime.timedelta(days=365)
            self.params["start_date"] = self.params["start_date"].strftime("%Y-%m-%d")
            self.params["end_date"] = self.params["submitted_date"]
            self.params["dates"] = "past_12"
            return True
        elif self.params["dates"] == "date_range":
            start = self.params["start_date"]
            end = self.params["end_date"]
            for val in [start, end]:
                if not is_a_date(val):
                    logger.warning("Error in date formatting, please check inputs")
                    return False
            return True
        elif self.params["dates"] == "all_dates":
            self.params["start_date"] = self.launchdt
            self.params["end_date"] = self.params["submitted_date"]
            return True

    def _url_format(self):
        query_params = {
            "query":self.params["query"].replace(" ", "%252B") + "%20",
            "jcode":self.params["source"].lower().strip(),
        }
        try:
            if self.params["add_cat"]:
                #TODO - remember to come back and check formatting
                query_params["subject_collection_code"] = self.params["categories"]
            if self.params["start_date"]:
                query_params["limit_from"] = self.params["start_date"]
            if self.params["end_date"]:
                query_params["limit_to"] = self.params["end_date"]
            query_params["numresults"] = "75"
            query_params["sort"] = "relevance-rank"
            query_params["format_result"] = "standard"
            search = query_params["query"]
            query_f1 = " ".join(f"{k}:{v}" for k, v in query_params.items() if k != "query")
            self.query_formatted = self.base_url + search + quote(query_f1)
            return True

            #NOTE: API
                #I find it hilarious that neither xrxiv left in a space in their api
                #to actually saerch the api as opposed to just dumping the lastest 
                #100 papers to be submitted.  Because of this idiocy, we will have 
                #to use the advanced search endpoint and parse the resultant 
                #html.  This also means we need to scrape each url because the
                #fundamental abstract data won't be present.  ugh.  idiots
                #TODO: Adapt SearchProgress progressbar
                    #I'll need a progress bar now if this 
                    #is going to take forever. 

                #api structure
                # https://api.medrxiv.org/details/[server]/[interval]/[cursor]/[format] 
                    # servers = duh
                    # interval - Date format whiiich looks like dates separated by /
                    # cursor - page iteration
                    # format - JSON or XML.  Json it is!
                #advancedsearch structure
                # https://www.biorxiv.org/search/anomaly%20
                # jcode%3Abiorxiv%20
                # subject_collection_code%3AClinical%20Trials%20
                # limit_from%3A2024-02-06%20
                # limit_to%3A2025-06-09%20
                # numresults%3A75%20
                # sort%3Arelevance-rank%20
                # format_result%3Astandard

        except Exception as e:
            logger.warning("Error in url query formatting")
            return False
    
    def _make_request(self, post:bool = False, doi_url:str = ""):
        chrome_version = np.random.randint(120, 135)
        if doi_url:
            baseurl = f"https://www.{self.server.lower()}.org"
        else:
            baseurl = self.base_url
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
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

        try:
            #First request
            if post:
                response = requests.post(self.query_formatted, headers=headers) 
            
            #Individual paper request
            elif doi_url:
                response = requests.get(doi_url, headers=headers)

            #Page Iteration
            else:
                response = requests.post(self.query_formatted + f"page={self.cursor}", headers=headers)
            
        except Exception as e:
            logger.warning(f"A general request error occured.  Check URL\n{e}")
            return None
        
        if response.status_code != 200:
            logger.warning(f'Status code: {response.status_code}')
            logger.warning(f'Reason: {response.reason}')
            return None, f"Status Code {response.status_code} Reason: {response.reason}"
        bs4ob = BeautifulSoup(response.text, "lxml")
        time.sleep(3) #Be nice to the servers
        return bs4ob

    def _query_xrxiv(self) -> dict:
        #Input validation checks
        formatted = self._date_format()
        classy = self._url_format()
        if not formatted or not classy:
            return None, "Error in formatting date or url"

        bs4ob = self._make_request(post=True) #True means make a post request
        paper_count = bs4ob.find("div", {"class":"highwire-search-summary"})

        if len(paper_count.text) > 0:
            if "No Results" in paper_count.text:
                return None, f"No papers returned for search ({self.params['query']}) in {self.params['source']} {self.params['field']}"
            pcount = paper_count.text.split()[0]
            pcount = int("".join(x for x in pcount if x.isnumeric()))
            self.paper_count = pcount 

        if pcount:
            new_papers = self._parse_query(bs4ob)
            logger.info(f'{len(new_papers)} papers returned from arxiv searching {self.params["query"]}')
            return new_papers, None

        else:
            message =f"No papers returned for search ({self.params['query']}) in {self.params['source']} {self.params['field']}"
            logger.warning(message)
            return None, message

    def _parse_query(self, bs4ob:BeautifulSoup):
        #Parse with the soups.  Will be tricky as I'll need to make multiple requests. 
        totalpapers = self.paper_count
        limit = self.params["limit"]
        paper_idx = 0
        while (paper_idx <= totalpapers) or (paper_idx <= limit): #If you are under either the requested limit, or the query limit continue extraction
            if self.cursor != 0:
                bs4ob = self._make_request()
            papers = bs4ob.find_all("li", {"class":lambda x: "search-result-highwire-citation" in x})
            for idx, result in enumerate(papers):
                paper = Paper()

                #Get the URL
                url = result.select("span", {"class":"highwire-cite-linked-title"})
                f_url = f"{self.base_url[:-8]}" + url[0].select("a")[0].get("href")
                paper.doi = f_url

                if url:
                    lil_req = self._make_request(doi_url=f_url)
                    paper.title = lil_req.find("h1", {"class":"highwire-cite-title"}).text.strip()
                    paper.id = str(idx) + "_" + paper.title
                    paper.pdf = paper.doi + ".full.pdf"

                    authors = lil_req.find_all("div", {"id":lambda x: x.startswith("q-tip")})
                    if authors:
                        paper.authors = {}
                        for author in authors:
                            name = author.find("div", {"class":"author-tooltip-name"})
                            paper.authors[name] = {}
                            #TODO - Write routines for all of these.  Ugh. 
                            paper.authors[name]["fullname"] = name
                            paper.authors[name]["url"]
                            paper.authors[name]["institution"]
                            paper.authors[name]["bio"]
                            #orcid ID's are stored in a separate container. 
                            #Meaning i would have to search and match the current name
                            #? Might be able to do the next sibling to get the name if it
                            #has an orcid id

                            paper.authors[name]["orcidid"]
                            
                    abstract = lil_req.find("div", {"class":"section abstract"})
                    if abstract:
                        paper.abstract = abstract.find("p").text

                    category = lil_req.find("span", {"class":"highwire-article-collection-term"})
                    if category:
                        paper.category = category.text.strip()

                    posted = lil_req.find("div", {"class":"panel-pane pane-custom pane-1"})
                    if posted:
                        post_date = posted.find("div", {"class":"pane-content"}).text.split("Posted\xa0")[1].strip().strip(".")
                        post_date_f = datetime.datetime.strptime(post_date, "%B %d, %Y")
                        paper.date_published = datetime.datetime.strftime(post_date_f, "%Y-%m-%d")
                    
                    paper.conference_info = self.params["source"]
                    
                    #TODO's
                    # keywords
                    # See if you can grab the interaction data.  That might be fun
                        # Looks like they have read abstracts, full, and pdf downloads
                        # Sweet! use m/year as key

                    # pull out if theirs a github repo in the info section
                    # also if they have a pub_link for if its been published. 
                        #Grab that too

                    # if "github" in paper.abstract:
                    #     #This regex will pull out a github.io or github.com link
                    #     pattern = r"((?:https?://)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)?github\.(?:com|io)(?:/[a-zA-Z0-9\._-]+)*)"
                    #     possiblematch = re.findall(pattern, paper.abstract)
                    #     if possiblematch:
                    #         paper.github_url = possiblematch[0]
                    
                    continue #to next paper
                else:
                    #Grab title
                    paper.title = result.find("span", {"class":lambda x:"title" in x}).text.strip()
                    paper.id = str(idx) + "_" + paper.title
                    
                    #Grab authors
                    authors = result.find_all("div", {"class":lambda x:"authors" in x}).text.strip()
                    if authors != None:
                        paper.authors = {str(ind) + "_" + x.text:x.text for ind, x in enumerate(authors)}

                    #
                    categories = result.find("div", attrs={"class":"tags is-inline-block"})
                    if categories != None:
                        paper.category = categories.text.split()

                    comments = result.find("p", attrs={"class": lambda e: e.startswith("comments")})
                    if comments != None:
                        comment_= comments.find("span", attrs={"class":"has-text-grey-dark mathjax"})
                        if comment_ != None:
                            paper.supplemental = comment_.text

                self.results.append(paper)
                paper_idx += 1

            self.cursor += 1


    # title   : str  | None = None
    # authors : list | None = None
    # keywords: list | None = None
    # category: list | None = None
    # abstract: str = ""
    # url     : str = ""
    # pdf     : str = ""
    # github_url     : str = ""  
    # supplemental   : str = ""  #general comments
    # date_published : str = ""  # mm-dd-yyyy
    # conference_info: str = ""  # e.g. arxiv

class bioRxiv(xRxivBase):
    def __init__(self, variables:dict):
        super().__init__(
            server = "bioRxiv",
            launchdt = "2013-01-01",
            base_url = "https://www.biorxiv.org/search/",
            params = variables
        )

class medRxiv(xRxivBase):
    def __init__(self, variables:dict):
        super().__init__(
            server = "medRxiv",
            launchdt = "2019-06-01",
            base_url = "https://www.medrxiv.org/search/",
            params = variables
    )

###############################  Date Functions ########################################
def is_a_date(datetext:str):
    try:
        datetime.datetime.strptime(datetext, "%Y-%m-%d")
        return True
    except Exception as e:
        logger.warning(f"date extraction error.  Check date format\n{e}")
        return False


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
    try:
        gpu_count = torch.cuda.device_count()
        if gpu_count > 1:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        # device = "cpu"
        #Trained on a bunch of bing queries
        if model_name == "Marco": #Polooooooo.
            model_path = "./data/models/marco/"
            if path.exists(model_path):
                model = SentenceTransformer(model_path, device = device)
                logger.info("Model loaded locally")
            else:
                mkdir("./data/models/marco")
                model = SentenceTransformer("msmarco-MiniLM-L6-v3", device = device)  #80M
                model.save_pretrained("./data/models/marco")
                logger.info("Model loaded and saved dynamically")

        # trained on finding similar papers.  Works better with abstracts but takes a really long time
        elif model_name == "Specter":
            model_path = "./data/models/specter"
            if path.exists(model_path):
                model = SentenceTransformer(model_path, device = device)
                logger.info("Model loaded locally")                
            else:
                mkdir("./data/models/specter")
                model = SentenceTransformer("allenai-specter", device = device) #425 MB
                model.save_pretrained("./data/models/specter")
                logger.info("Model loaded and saved dynamically")

        return model, device
        
    except Exception as e:
        raise ValueError(f"error:{e}\nYou probably to install sentence-transformers for model {model_name}")
