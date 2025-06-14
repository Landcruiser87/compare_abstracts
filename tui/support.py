#main libraries
import datetime
import time
import logging
import os
import json
import numpy as np
import requests
from bs4 import BeautifulSoup
from rich import print
from rich.tree import Tree
from rich.text import Text
from rich.markup import escape
from rich.filesize import decimal
from rich.console import Console
from rich.logging import RichHandler
from pathlib import Path, PurePath

################################# Logger functions ####################################
#FUNCTION Logging Futures
def get_file_handler(log_dir:Path)->logging.FileHandler:
    """Assigns the saved file logger format and location to be saved

    Args:
        log_dir (Path): Path to where you want the log saved

    Returns:
        filehandler(handler): This will handle the logger's format and file management
    """	
    log_format = "%(asctime)s|%(levelname)-8s|%(lineno)-4d|%(funcName)-13s|%(message)-108s|" 
                 #f"%(asctime)s - [%(levelname)s] - (%(funcName)s(%(lineno)d)) - %(message)s"
    # current_date = time.strftime("%m_%d_%Y")
    file_handler = logging.FileHandler(log_dir)
    file_handler.setFormatter(logging.Formatter(log_format, "%m-%d-%Y %H:%M:%S"))
    return file_handler

def get_rich_handler(console:Console)-> RichHandler:
    """Assigns the rich format that prints out to your terminal

    Args:
        console (Console): Reference to your terminal

    Returns:
        rh(RichHandler): This will format your terminal output
    """
    rich_format = "|%(funcName)-13s| %(message)s"
    rh = RichHandler(console=console)
    rh.setFormatter(logging.Formatter(rich_format))
    return rh

def get_logger(console:Console, log_dir:Path)->logging.Logger:
    """Loads logger instance.  When given a path and access to the terminal output.  The logger will save a log of all records, as well as print it out to your terminal. Propogate set to False assigns all captured log messages to both handlers.

    Args:
        log_dir (Path): Path you want the logs saved
        console (Console): Reference to your terminal

    Returns:
        logger: Returns custom logger object.  Info level reporting with a file handler and rich handler to properly terminal print
    """	
    #Load logger and set basic level
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #Load file handler for how to format the log file.
    file_handler = get_file_handler(log_dir)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    #Load rich handler for how to display the log in the console
    # rich_handler = get_rich_handler(console)
    # rich_handler.setLevel(logging.INFO)
    # logger.addHandler(rich_handler)
    logger.propagate = False
    return logger

#FUNCTION timer
################################# Timing Funcs ####################################
def log_time(fn):
    """Decorator timing function.  Accepts any function and returns a logging
    statement with the amount of time it took to run. DJ, I use this code everywhere still.  Thank you bud!

    Args:
        fn (function): Input function you want to time
    """	
    def inner(*args, **kwargs):
        tnow = time.time()
        out = fn(*args, **kwargs)
        te = time.time()
        took = round(te - tnow, 2)
        if took <= 60:
            logging.info(f"{fn.__name__} ran in {took:.3f}s")
        elif took <= 3600:
            logging.info(f"{fn.__name__} ran in {(took)/60:.3f}m")		
        else:
            logging.info(f"{fn.__name__} ran in {(took)/3600:.3f}h")
        return out
    return inner

#FUNCTION get time
def get_time():
    """Function for getting current time

    Returns:
        t_adjusted (str): String of current time
    """
    current_t_s = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    current_t = datetime.datetime.strptime(current_t_s, "%m-%d-%Y-%H-%M-%S")
    return current_t

########################## Saving funcs ##########################################
# #FUNCTION save results
# def save_result(name:str, processed:pd.DataFrame, logger:logging):
#     """Save Routine.  Takes in name of file and processed dataframe.  Saves it to the data/cleaned folder. 

#     Args:
#         name (str): Name of file being converted
#         processed (pd.DataFrame): Processed dataframe of translated codes
#     """	
#     spath = f"./data/cleaned/{name}"
#     processed.to_csv(spath, mode='w', header=0, encoding='utf-8')
#     logger.info(f"CSV for file {spath} saved")

################################# Size Funcs ############################################

def sizeofobject(folder)->str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(folder) < 1024:
            return f"{folder:4.1f} {unit}"
        folder /= 1024.0
    return f"{folder:.1f} PB"

def getfoldersize(folder:Path):
    fsize = 0
    for root, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(folder,f)
            fsize += os.stat(fp).st_size

    return sizeofobject(fsize)

def getpapercount(file:Path):
    with open(file, "r") as jfile:
        jfile = json.loads(jfile.read())
        numpapers = len(jfile.keys())

    return numpapers

################################# TUI Funcs ############################################

#FUNCTION Launch TUI
def launch_tui():
    try:
        directory = PurePath(Path.cwd(), Path("./data/conferences/"))

    except IndexError:
        logger.info("[b]Usage:[/] python tree.py <DIRECTORY>")
    else:
        tree = Tree(
            f":open_file_folder: [link file://{directory}]{directory}",
            guide_style="bold bright_blue",
        )
        files = walk_directory(Path(directory), tree)
        print(tree)
    # logger.info(f"There are {pcount} papers in {directory}")
    question ="What file would you like to load?\n"
    file_choice = console.input(f"{question}")
    if file_choice.isnumeric():
        file_to_load = files[int(file_choice) - 1]
        #check output directory exists
        return file_to_load
    elif file_choice is None:
        return None

    else:
        raise ValueError("Please restart and select an integer of the file you'd like to import")
    
#FUNCTION Walk Directory
def walk_directory(directory: Path, tree: Tree) -> None:
    """Build a Tree with directory contents.
    Source Code: https://github.com/Textualize/rich/blob/master/examples/tree.py

    """
    # Sort dirs first then by filename
    paths = sorted(
        Path(directory).iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
    )
    idx = 1
    # paper_count = 0
    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        # Just list the CAM folders
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            file_size = getfoldersize(path)
            branch = tree.add(
                f"[bold green]{idx} [/bold green][bold magenta]:open_file_folder: [link file://{path}]{escape(path.name)}[/bold magenta] [bold blue]{file_size}[/bold blue]",
                style=style,
                guide_style=style,
            )
            
            # walk_directory(path, branch)
        else:
            # paper_count += getpapercount(path)
            text_filename = Text(path.name, "green")
            text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            if path.name.split(".")[0].split("_")[1] in MAIN_CONFERENCES:
                icon = "🔥 "
            elif path.name.split(".")[0].split("_")[1] in SUB_CONFERENCES:
                icon = "🐍 "
            elif path.suffix == ".mib":
                icon = "👽 "
            else:
                icon = "🔫 "
            tree.add(Text(f'{idx} ', "blue") + Text(icon) + text_filename)
        idx += 1

    return paths

def list_datasets() -> list[tuple]:
    """Main function is list available datasources

    Args:
        paths list[Path]: List of pathlib Path's

    Returns:
        results list[tuple]: Returns a list of file names with their index as tuples
    """
    results = []
    filenum = 0
    s_paths = [Path("./data/conferences/"), Path("./data/searches/")]
    for directory in s_paths:
        paths = sorted(
            directory.iterdir(),
            key=lambda path: (path.is_file(), path.name.lower()),
        )
        for val in paths:
            results.append((val.stem, filenum))
            filenum += 1

    return results

########################## Saving funcs ##########################################

class NumpyArrayEncoder(json.JSONEncoder):
    """Custom numpy JSON Encoder.  Takes in any type from an array and formats it to something that can be JSON serialized. Source Code found here. https://pynative.com/python-serialize-numpy-ndarray-into-json/
    
    Args:
        json (object): Json serialized format
    """	
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return obj.__dict__
        elif isinstance(obj, str):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return datetime.datetime.strftime(obj, "%m-%d-%Y-%H-%M-%S")
        else:
            return super(NumpyArrayEncoder, self).default(obj)
    
#FUNCTION Save JSON
def save_data(search_name:str, data:dict):
    result_json = json.dumps(data, indent=2, cls=NumpyArrayEncoder)
    with open(f"./data/searches/{search_name}.json", "w") as outf:
        outf.write(result_json)

#FUNCTION Load JSON
def load_json(fp:str)->json:
    """Loads the saved JSON arXiv categories

    Args:
        fp (str): File path for ze loading

    Returns:
        jsondata (JSON): dictionary version of saved JSON
    """    
    if os.path.exists(fp):
        with open(fp, "r") as f:
            jsondata = json.loads(f.read())
            return jsondata	

########################## Web functions ##########################################
def get_categories(result:BeautifulSoup) -> dict:
    """[Ingest XML of summary page for articles info]

    Args:
        result (BeautifulSoup object): html of apartments page

    Returns:
        categories (dict): [Dictionary of the arXiv categories]
    """
    #Base data container
    categories = {}

    #Iterate over taxonomy children
    for child in result.contents:
        #If its an H2 tag, its a category
        if child.name == "h2":
            key = child.text
            categories[key] = {}
            continue
        #If its blank, skip it
        elif child == '\n':
            continue
        #If its the body, extract the sub categories we want        
        elif child.attrs.get("class")[0] == "accordion-body":
            containers = child.find_all("div", class_="columns divided")
            for subchild in containers:
                code_search = subchild.find("h4")
                code = code_search.text.split()[0].strip()
                abb_search = subchild.find("span")
                abb = abb_search.text.strip("()")
                desc_search = subchild.find("p")
                desc = desc_search.text.strip()
                categories[key][code] = (abb, desc)

    return categories

def rebuild_taxonomy() -> dict:
    url = "https://www.arxiv.org/category_taxonomy"
    referrer = "https://info.arxiv.org/"
    chrome_version = np.random.randint(120, 137)
    headers = {
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': f'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36',
        'sec-ch-ua': f'"Not)A;Brand";v="99", "Google Chrome";v={chrome_version}, "Chromium";v={chrome_version}',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'referer': referrer,
        'Content-Type': 'text/html,application/xhtml+xml,application/xml'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    #Parse the XML
    bs4ob = BeautifulSoup(response.text, features="lxml")

    #Find all the categories
    results = bs4ob.find("div", {"id":"category_taxonomy_list"})
    if results:
        categories = get_categories(results)
        logger.debug(f'categories successfully returned from {url}')
        return categories
            
    else:
        logger.warning(f"An error occured and categories could not be extracted. Check DOM for updated field names")

def load_taxonomy(search:bool=False):
    try:
        if search:
            categories = rebuild_taxonomy()
            cat_json = json.dumps(categories, indent=2, cls=NumpyArrayEncoder)
            with open(f"./data/conferences/arxiv_cat.json", "w") as outf:
                outf.write(cat_json)

        else:
            path = "./data/arxiv_cat.json"
            if os.path.exists(path):
                categories = load_json(path)
            else:
                logger.warning(f"An error occured loading the arx-cat.json file")

        return categories 
    
    except Exception as e:
        logger.warning("Arxiv Categories were not loaded properly")
        logger.warning(f"Error: {e}")
        logger.warning("To rebuild Taxonomy, set initial search variable to True")

########################## Global Variables for import ##########################################

#logger/console stuffs
date_json = get_time().strftime("%m-%d-%Y_%H-%M-%S")
console = Console(color_system="auto", stderr=True)
logger = get_logger(console, log_dir=f"data/logs/tui/{date_json}.log")

#Confernces
MAIN_CONFERENCES  = ["ICML", "ICLR", "NEURIPS"]
SUB_CONFERENCES   =  ["COLT", "AISTATS", "AAAI", "CHIL", "ML4H", "ICCV"] 
SEARCH_FIELDS = ["title", "keywords", "topic", "abstract"]  

#Metrics for asymetric similarity search
SEARCH_MODELS = ["Fuzzy", "Cosine", "Word2Vec", "Marco", "Specter"]
MODEL_DESC = [
    "Fuzzy matching like regex.  Warning: Very slow when run against the abstract field", 
    "Very fast and good for basic retrieval.  Uses TF-IDF with L1 regularization", 
    "Using the standard spacy pipeline, calculates a cosine sim with more detailed embeddings", 
    "Good for Asymetric Semantic Search.  Slower than above, but more accurate. Available for GPU",
    "Meant for comparing scientific papers.   Runs quite slowly on abstracts. Available for GPU"
]
#arXiv Params
ARXIV_FIELDS = ["Title", "Abstract", "Author(s)",  "Comments", "DOI", "arXiv id", "ORCID"]
ARXIV_SUBJECTS = ["Computer Science", "Economics", "Electrical Engineering and Systems Science", "Mathematics", "Physics", "Quantitative Biology", "Quantitative Finance", "Statistics"]
ARXIV_DATES = ["All Dates", "Past 12 Months", "Specific Year", "Date Range"]
ARXIV_AREAS = load_taxonomy()

XARXIV_FIELDS = ["Title", "Abstract", "Author(s)", "Abstract|Title", "Text|Abstract|Title"]  
XARXIV_SOURCES = ["bioRxiv", "medRxiv", "both"]
XARXIV_SORT = ["Best match", "Oldest first", "Newest first", "Popularity"]
BIOARXIV_SUBJECTS =[
    "Animal Behavior and Cognition", "Biochemistry", "Bioengineering",
    "Bioinformatics", "Biophysics", "Cancer Biology", "Cell Biology",
    "Clinical Trials", "Developmental Biology", "Ecology", "Epidemiology",
    "Evolutionary Biology", "Genetics", "Genomics", "Immunology", "Microbiology", 
    "Molecular Biology", "Neuroscience", "Paleontology", "Pathology", 
    "Pharmacology and Toxicology", "Physiology", "Plant Biology", 
    "Scientific Communication and Education", "Synthetic Biology", "Systems Biology", "Zoology"
]

MEDARXIV_SUBJECTS= [
    "Addiction Medicine", "Allergy and Immunology", "Anesthesia",
    "Cardiovascular Medicine", "Dentistry and Oral Medicine", "Dermatology",
    "Emergency Medicine", "Endocrinology (including Diabetes Mellitus and Metabolic Disease)", 
    "Epidemiology", "Forensic Medicine", "Gastroenterology", "Genetic and Genomic Medicine", "Geriatric Medicine",
    "Health Economics", "Health Informatics", "Health Policy", 
    "Health Systems and Quality Improvement", "Hematology", "HIV/AIDS", 
    "Infectious Diseases (except HIV/AIDS)", "Intensive Care and Critical Care Medicine", "Medical Education",
    "Medical Ethics", "Nephrology", "Neurology", "Nursing",
    "Nutrition", "Obstetrics and Gynecology", "Occupational and Environmental Health",
    "Oncology", "Ophthalmology", "Orthopedics", "Otolaryngology",
    "Pain Medicine", "Palliative Medicine", "Pathology", "Pediatrics",
    "Pharmacology and Therapeutics", "Primary Care Research", "Psychiatry and Clinical Psychology", 
    "Public and Global Health", "Radiology and Imaging",
    "Rehabilitation Medicine and Physical Therapy", "Respiratory Medicine",
    "Rheumatology", "Sexual and Reproductive Health", "Sports Medicine",
    "Surgery", "Toxicology", "Transplantation", "Urology"
]