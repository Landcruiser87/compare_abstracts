import json
import support
import requests
import numpy as np
from support import logger, console, log_time
# I might be able to do this with just dictionaries. 
# Keeping for now, just in case.
# # from dataclasses import dataclass, field
# #Dataclass container
# @dataclass
# class ML_Paper():
#     id          : str
#     url         : str
#     title       : str
#     abstract    : str
#     topic       : str
#     session     : str
#     conference  : str
#     event_type  : str
#     paper_url   : str
#     pub_date    : datetime.datetime
#     virtual_site_url : str
#     authors          : dict = field(default_factory=lambda:{})


CHROME_VERSION = np.random.randint(120, 132)

#FUNCTION Filter result
def extract_json(json_data:json)->dict:
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
        for key in base_keys:
            temp = json_data["results"][id].get(key)
            if temp:
                base_dict[id][key] = temp

    #NOTE: Possible cool data within neurips
    #could be cool stuff in event media, but save for later. 

    return base_dict

#FUNCTION Request Conference
def request_conf(conference:str, year:int):
    conf_dict={
        "NEURIPS":{
            "name":"Conference and Workshop on Neural Information Processing Systems",
            "abbrv":"NEURIPS",
            "url":f"https://neurips.cc/static/virtual/data/neurips-{year}-orals-posters.json",
            "headers":{
                "authority":f"https://neurips.cc/static/virtual/data/neurips-{year}-orals-posters.json",
                "method":"GET",
                "path":f"/static/virtual/data/neurips-{year}-orals-posters.json",
                "scheme":"https",
                "accept":"*/*",
                "accept-encoding":"gzip,deflate,br,zstd",
                "accept-language":"en-US,en;q=0.9",
                "referer":f"https://neurips.cc/virtual/{year}/papers.html?filter=titles",
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
            "url":f"https://icml.cc/static/virtual/data/icml-{year}-orals-posters.json",
            "headers":{
                "authority":f"https://icml.cc/static/virtual/data/icml-{year}-orals-posters.json",
                "method":"GET",
                "path":f"/static/virtual/data/neurips-{year}-orals-posters.json",
                "scheme":"https",
                "accept":"*/*",
                "accept-encoding":"gzip,deflate,br,zstd",
                "accept-language":"en-US,en;q=0.9",
                "referer":f"https://icml.cc/virtual/{year}/papers.html?filter=titles",
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
            "url":f"https://iclr.cc/static/virtual/data/iclr-{year}-orals-posters.json",
            "headers":{
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Referer": f"https://iclr.cc/virtual/{year}/papers.html?filter=titles",
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

    url = conf_dict[conference]["url"]
    headers = conf_dict[conference]["headers"]
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        logger.debug(f"request successful for {url}, parsing data")
        resp_json = resp.json()
        results = extract_json(resp_json)
    else:
        # If there's an error, log it and return no data for that conference
        logger.warning(f"Status code: {resp.status_code}")
        logger.warning(f"Reason: {resp.reason}")
        results = None

    return results


#NOTE START PROGRAM
#FUNCTION main
@log_time
def main():
    """Main driver code for program"""
    main_conferences = ["ICLR", "NEURIPS", "ICML"]# ,"ml4h"]
    years = range(2013, 2025)
    global prog, task, total_stops
    total_stops = 0
    prog, task = support.mainspinner(console, len(main_conferences)*len(years)) 

    with prog:
        for year in years:
            logger.debug(f"beginning search for {year}")
            for conference in main_conferences:
                logger.debug(f"searching {conference} {year}")
                prog.update(task_id=task, description=f"[green]{year}:{conference}", advance=1)
                result = request_conf(conference, year)
                if result:
                    support.save_data(result, conference, year)		
                    logger.debug(f"{conference} has been converted and saved")
                else:
                    logger.info(f"{conference} data not available.")

                support.add_spin_subt(prog, "He who takes naps, gets 200's", np.random.randint(3, 6))

    logger.warning(f"Conferences from {years.start} to {years.stop} searched.  Shutting down program")

if __name__ == "__main__":
    main()

    #Go here to scrape other conferences. 
        #https://proceedings.mlr.press/
        #Ummm each conf on the above site have RSS feeds.  I can pull papers from all of them

    #Other future conferences to add


#Ryan idea's for embedding
# gemma/bert embed
# tsne
# plot first two components. 
