import requests
import json
import support
import time
import numpy as np
from support import logger, console, log_time
# from bs4 import BeautifulSoup, only installing if we need it. 


YEAR = 2024  #! CHANGE ME
CHROME_VERSION = np.random.randint(120, 132)
CONF_DICT={
    "NEURIPS":{
        "name":"Conference and Workshop on Neural Information Processing Systems",
        "abbrv":"NEURIPS",
        "url":f"https://neurips.cc/static/virtual/data/neurips-{YEAR}-orals-posters.json",
        "headers":{
            "authority":f"https://neurips.cc/static/virtual/data/neurips-{YEAR}-orals-posters.json",
            "method":"GET",
            "path":f"/static/virtual/data/neurips-{YEAR}-orals-posters.json",
            "scheme":"https",
            "accept":"*/*",
            "accept-encoding":"gzip,deflate,br,zstd",
            "accept-language":"en-US,en;q=0.9",
            "referer":f"https://neurips.cc/virtual/{YEAR}/papers.html?filter=titles",
            "sec-ch-ua":f'"Chromium";v="{CHROME_VERSION}", "Not(A:Brand";v="24", "Google Chrome";v="{CHROME_VERSION}"',
            "sec-ch-ua-Mobile":"?0",
            "sec-ch-ua-platform":"Windows",
            "sec-fetch-dest":"empty",
            "sec-fetch-mode":"cors",
            "sec-fetch-site":"same-origin",
            "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36',
            "x-requested-with":"XMLHttpRequest"
            }
    },
    "ICML":{
        "name":"International Conference of Machine Learning",
        "abbrv":"ICML",
        "url":f"https://icml.cc/static/virtual/data/icml-{YEAR}-orals-posters.json",
        "headers":{
            "authority":f"https://icml.cc/static/virtual/data/icml-{YEAR}-orals-posters.json",
            "method":"GET",
            "path":f"/static/virtual/data/neurips-{YEAR}-orals-posters.json",
            "scheme":"https",
            "accept":"*/*",
            "accept-encoding":"gzip,deflate,br,zstd",
            "accept-language":"en-US,en;q=0.9",
            "referer":f"https://icml.cc/virtual/{YEAR}/papers.html?filter=titles",
            "sec-ch-ua":f'"Chromium";v="{CHROME_VERSION}", "Not(A:Brand";v="24", "Google Chrome";v="{CHROME_VERSION}"',
            "sec-ch-ua-Mobile":"?0",
            "sec-ch-ua-platform":"Windows",
            "sec-fetch-dest":"empty",
            "sec-fetch-mode":"cors",
            "sec-fetch-site":"same-origin",
            "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36",
            "x-requested-with":"XMLHttpRequest"
            }
    },
    "ML4H":{
        "name":"Machine Learning for Health",
        "abbrv":"ML4H",
        "url":"stuff",
        "headers":"morestuff"
    }, 
    "ICLR":{
        "name":"International Conference of Learning Representations",
        "abbrv":"ICLR",
        "url":f"https://iclr.cc/static/virtual/data/iclr-{YEAR}-orals-posters.json",
        "headers":{
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://iclr.cc/virtual/{YEAR}/papers.html?filter=titles",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": f"'Chromium';v='{CHROME_VERSION}', 'Not:A-Brand';v='24', 'Google Chrome';v='{CHROME_VERSION}'",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "'Windows'",
        }
    }
}

import requests
#FUNCTION Filter result
def extract_json(json_data:json)->dict:
    # Possible cool data within neuripps
    ids = list(range(json_data["count"]))
    base_keys = ["id","name","author","abstract","keywords","topic","session","event_type","virtualsite_url","url","paper_url"]
    base_dict = {val:{key:"" for key in base_keys} for val in ids}
    for id in ids:
        authors = range(len(json_data['results'][id]['authors']))
        base_dict[id]["author"] = {author:{} for author in authors} 
        #Grab author info
        for author in authors:
            auth_info = json_data["results"][id]["authors"][author]
            base_dict[id]["author"][author].update(**auth_info)
        
        #Grab other keys we want from the paper
        for term in base_keys:
            temp = json_data["results"][id].get(term)
            if temp:
                base_dict[id][term] = temp
    #could be cool stuff in event media, but save for later. 
    return base_dict


def extract_w_soup():
    pass

#FUNCTION Request Conference
def request_conf(conference:str):
    url = CONF_DICT[conference]["url"]
    headers = CONF_DICT[conference]["headers"]
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        resp_json = resp.json()
        if conference != "ml4h":
            results = extract_json(resp_json)
        else:
            results = extract_w_soup(resp_json)
    else:
        logger.warning(f"\nServer Error\n{url}\nResponse: {resp.status_code}\n{resp.reason}")
        results = None

    return results


#NOTE START PROGRAM
#FUNCTION main
@log_time
def main():
    """Main driver code for program"""
    logger.debug(f"Beginning search for {YEAR}")
    main_conferences = ["ICLR", "NEURIPS", "ICML"]# ,"ml4h"] 

    for conference in main_conferences:
        result = request_conf(conference)
        if result:
            support.save_data(result, conference, YEAR)		
            logger.debug(f"{conference} has been converted and saved")
        else:
            logger.info(f"{conference} had no data.")
        time.sleep(np.random.randint(2, 4))
    logger.warning(f'All conferences have been searched.  Shutting down program')

if __name__ == "__main__":
    main()

    #Go here to scrape other conferences. 
        #https://proceedings.mlr.press/
        #Ummm each conf on the above site have RSS feeds.  I can pull papers from all of them

    #Other future conferences to add

    #Grab abstracts from here. 
    #https://neurips.cc/virtual/2023/papers.html?filter=titles


#Ryan idea's for embedding
# gemma/bert embed
# tsne
# plot first two components. 
