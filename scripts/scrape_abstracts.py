import re
import json
import support
import requests
import numpy as np
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from itertools import cycle
from support import console, logger, log_time

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

MAIN_CONFERENCES  = ["ICML", "ICLR", "NEURIPS"]
SUB_CONFERENCES   =  ["COLT", "AISTATS", "AAAI", "CHIL", "ML4H", "ECCV"] #"CLDD"-Got an xml error for 2024
FUN_STATUS_UPDATE = cycle(["Patience Iago", "Phenominal COSMIC POWER", "Iiiiiity bitty living space", "Books, i've read these books", "Your conclusions were all wrong Ryan", "Let it go Indiana", "Duuuude", "wheres my car", "I wanna talk to sampson!!"])

#FUNCTION Request Conference
def request_conf(conference:str, year:int=None, version:str=""):
    """Function to request a single years conference papers

    Args:
        conference (str): Conference of interest
        year (int): Year of interest

    Returns:
        results (dict): Dictionary of papers from each conference
    """    
    chrome_version = np.random.randint(120, 132)
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
                "sec-ch-ua":f'"Chromium";v="{chrome_version}", "Not(A:Brand";v="24", "Google Chrome";v="{chrome_version}"',
                "sec-ch-ua-Mobile":"?0",
                "sec-ch-ua-platform":"Windows",
                "sec-fetch-dest":"empty",
                "sec-fetch-mode":"cors",
                "sec-fetch-site":"same-origin",
                "user-agent": f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
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
                "sec-ch-ua":f'"Chromium";v="{chrome_version}", "Not(A:Brand";v="24", "Google Chrome";v="{chrome_version}"',
                "sec-ch-ua-Mobile":"?0",
                "sec-ch-ua-platform":"Windows",
                "sec-fetch-dest":"empty",
                "sec-fetch-mode":"cors",
                "sec-fetch-site":"same-origin",
                "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
                "x-requested-with":"XMLHttpRequest"
            }
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
                "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "sec-ch-ua": f"'Chromium';v='{chrome_version}', 'Not:A-Brand';v='24', 'Google Chrome';v='{chrome_version}'",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "'Windows'",
            }
        },
        "PMLR":{
            "name":"Proceedings in Machine Learning Research",
            "abbrv":"PMLR",
            "url":f"https://proceedings.mlr.press//assets/rss/feed.xml",
            "headers" : {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "max-age=0",
                "if-modified-since": "Tue, 18 Feb 2025 09:52:46 GMT",
                "if-none-match": "W/'67b4586e-111f4'",
                "priority": "u=0, i",
                "referer": "https://proceedings.mlr.press/",
                "sec-ch-ua": f"'Chromium';v={chrome_version}, 'Not:A-Brand';v='24', 'Google Chrome';v={chrome_version}",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "'Windows'",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
            }
        },
        "IND_CONF":{
            "name":"Individual conference request",
            "abbrv":"PMLR",
            "url":f"https://proceedings.mlr.press//{version}//assets/rss/feed.xml",
            "headers" : {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "max-age=0",
                "if-modified-since": "Tue, 18 Feb 2025 09:52:46 GMT",
                "if-none-match": "W/'67b4586e-111f4'",
                "priority": "u=0, i",
                "referer": "https://proceedings.mlr.press/",
                "sec-ch-ua": f"'Chromium';v={chrome_version}, 'Not:A-Brand';v='24', 'Google Chrome';v={chrome_version}",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "'Windows'",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
            }
        },        
        "ML4H":{
            "name":"Machine Learning for Health",
            "abbrv":"ML4H",
            "url":"stuff",
            "headers":"morestuff"
        }
    }
    if version:
        url = conf_dict["IND_CONF"]["url"]
        headers = conf_dict["IND_CONF"]["headers"]
        resp = requests.get(url, headers=headers)
        
    else:
        url = conf_dict[conference]["url"]
        headers = conf_dict[conference]["headers"]
        resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        # If there's an error, log it and return no data for that conference
        logger.warning(f"Status code: {resp.status_code}")
        logger.warning(f"Reason: {resp.reason}")
        results = None
    else:
        logger.debug(f"request successful for {url}, parsing data")
        #If its the overall scrape of PLMR
        if conference == "PMLR":
            results = parse_all(resp.content, year_limit=year)
        #If its a main conference
        elif conference in MAIN_CONFERENCES:
            resp_json = resp.json()
            results = extract_json(resp_json, url)
        #If its a sub conference
        else:
            results = parse_conf(resp.content)

    return results

def request_paper(paper:dict, version:str) -> dict | None:
    chrome_version = np.random.randint(120, 132)
    paper_dict = {
        "name":"Individual paper request",
        "abbrv":"PMLR",
        "url":paper["url"],
        "headers" : {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "referer": f"https://proceedings.mlr.press/{version}/",
            "sec-ch-ua": f"'Chromium';v={chrome_version}, 'Not:A-Brand';v='24', 'Google Chrome';v={chrome_version}",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "'Windows'",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
        }
    }

    url = paper_dict["url"]
    headers = paper_dict["headers"]
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        # If there's an error, log it and return no data for that conference
        logger.warning(f"Status code: {resp.status_code}")
        logger.warning(f"Reason: {resp.reason}")

    else:
        logger.debug(f"request successful for {url}, parsing data")
        extras = parse_paper(resp.text)
        paper.update(**extras)

    return paper

############################### Data Extraction Functions ##################
#FUNCTION Filter result
def extract_json(json_data:json, url:str)->dict:
    ids = list(range(json_data["count"]))
    base_keys = ["id","name","author","abstract","keywords","topic","session","event_type","virtualsite_url","url","paper_url", "paper_pdf_url", "sourceurl"]
    base_dict = {str(val) + "_" + json_data["results"][val]["name"]:{key:"" for key in base_keys} for val in ids}
    for id, idx in zip(base_dict.keys(), ids):
        authors = [str(x) + "_" + json_data['results'][idx]['authors'][x]["fullname"] for x in range(len(json_data['results'][idx]['authors']))]
        base_dict[id]["author"] = {author:{} for author in authors} 
        #Grab author info
        for num, author in enumerate(authors):
            auth_info = json_data["results"][idx]["authors"][num]
            base_dict[id]["author"][author].update(**auth_info)
        
        #Grab other keys we want from the paper
        for key in base_keys:
            temp = json_data["results"][idx].get(key)
            if key == "virtualsite_url" and temp:
                base_dict[id][key] = "https://"+ url.split("/")[2] + temp
            elif temp:
                base_dict[id][key] = temp

    return base_dict

def parse_all(xml:str, year_limit:int=2010) -> dict:
    """parses xml from initial RSS feed of possible conferences

    Args:
        xml (str): _description_
        year_limit (int, optional): _description_. Defaults to 2016.

    Returns:
        dict: _description_
    """    
    results = {}
    root = ET.fromstring(xml)
    for paper in root.findall("channel/item"):
        description = paper.find("description").text
        for conf in SUB_CONFERENCES:
            if conf in description:
                #regex for any year (four consecutive numbers) between 1900 and 2100
                pattern = r"\b(19[0-9]{2}|20[0-9]{2}|2100)\b"
                match = re.findall(pattern, description)
                if match:
                    if int(match[0]) >= year_limit:
                        year = match[0]
                    else:
                        continue
                else:
                    continue
                results[year + "_" + conf]= paper.find("link").text
    return results

def parse_conf(xml:str):
    results = {}
    root = ET.fromstring(xml)
    for idx, paper in enumerate(root.findall("channel/item")):
        key = paper.find("title").text
        key = "".join(str(x) for x in key if x.isalnum() | x.isspace())
        key = str(idx) + "_" + key.strip()
        url = paper.find("link").text
        results[key] = {}
        results[key]["title"] = paper.find("title").text
        results[key]["abstract"] = paper.find("description").text
        results[key]["url"] = paper.find("link").text
        results[key]["id"] = paper.find("guid").text
        user = url.split("/")[-1].split(".")[0]
        results[key]["pdf"] = url[:url.rindex(".")] + "/" + user + ".pdf"

    return results

def parse_paper(page_text:str):
    temp = {
        "authors":{},
        "pmlr_pdf":"",
        "github_url":"",
        "conf_info":"",
        "supplemental":""
    }
    bs4ob = BeautifulSoup(page_text, features="lxml")
    authors = bs4ob.find("span", class_="authors")
    if authors:
        auth_l = authors.text.split(",")
        for idx, author in enumerate(auth_l):
            temp["authors"][str(idx) + "_" + author.strip()] = author.strip()

    extras = bs4ob.find_all("li")
    if extras:
        pullbacks = ["Software", "Download PDF", "Supplementary PDF"]
        for extra in extras:
            if extra.text in pullbacks:
                funstuff = extra.find("a").get("href")
                if extra.text == "Software":
                    temp["github_url"] = funstuff
                elif extra.text == "Download PDF":
                    temp["pmlr_pdf"] = funstuff
                elif extra.text == "Supplmentary PDF":
                    temp["supplemental"] = funstuff

    #Pull in Conf into as well
    info = bs4ob.find("div", id="info")
    if info:
        temp["conf_info"] = info.text.strip()

    return temp
    #Things I need
    # Authors, github, poster url

    #NOTE Needs to return updated dictionary
    #Also might need bs4 to parse the HTML..  Need to look for json build.


#NOTE START PROGRAM
#FUNCTION main
@log_time
def main():
    """Main driver code for program"""
    years = range(2022, 2025)
    logger.debug("searching PMLR")
    PMLR = request_conf("PMLR", year=years.start)
    global prog, task
    prog, task = support.mainspinner(console, len(MAIN_CONFERENCES)*len(years) + len(PMLR.keys())) 

    with prog:
        for year in years:
            #Search Main conferences
            logger.debug(f"searching main conferences in {year}")
            for conference in MAIN_CONFERENCES:
                logger.info(f"{conference:7s}:{year} searching")
                prog.update(task_id=task, description=f"[green]{year}[/green]:[yellow]{conference}[/yellow]", advance=1)
                result = request_conf(conference, year)
                if result:
                    support.save_data(result, conference, year)		
                else:
                    logger.warning(f"{conference:7s}:{year} not available.")
                support.add_spin_subt(prog, f"[purple]{next(FUN_STATUS_UPDATE)}[/purple]", np.random.randint(3, 6))
        logger.warning(f"Main conferences from {years.start} to {years.stop} searched.")

        #Search Sub conferences
        for conference, link in PMLR.items():
            year, conf = conference.split("_")
            conf = conf.strip()
            prog.update(task_id=task, description=f"[green]{year}[/green]:[yellow]{conf}[/yellow]", advance=1)
            version = link.split("/")[-1]
            logger.info(f"{conf:7s}:{year} searching")
            results = request_conf(link, version=version)
            
            #Author / Git extraction
            for title, paperinfo in results.items():
                results[title] = request_paper(paperinfo, version)
                logger.info(f"parsing {title}")
                support.add_spin_subt(prog, f"[green]{title:30s}[/green]", np.random.randint(1, 8))

            support.save_data(results, conf, year)
            support.add_spin_subt(prog, f"[yellow]{next(FUN_STATUS_UPDATE)}[/yellow]", np.random.randint(3, 6))
        logger.warning(f"Sub conferences from {years.start} to {years.stop} searched.")

if __name__ == "__main__":
    main()

#TODO - remember to fix the keys up to 2022.  Somehow you forgot to include the space in front of the title.  doh!

    #Go here to scrape other conferences. 
        #https://proceedings.mlr.press/
        #Ummm each conf on the above site have RSS feeds.  I can pull papers from all of them!!!
    #Other future conferences to add