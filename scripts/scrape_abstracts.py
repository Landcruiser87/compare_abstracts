import numpy as np
import pandas as pd
from rich.logging import RichHandler
from rich.console import Console
from time import strftime, sleep
from collections import deque
import os
import logging
import requests
import json
import time	
# from bs4 import BeautifulSoup, only installing if we need it. 

#Grab abstracts from here. 
#https://neurips.cc/virtual/2023/papers.html?filter=titles

#Logging setup stuffs
current_date = strftime("%m-%d-%Y_%H-%M-%S")
FORMAT = "%(asctime)s|%(levelname)s|%(funcName)s|%(lineno)d|%(message)s" #[%(name)s]
FORMAT_RICH = "%(funcName)s|%(lineno)d|%(message)s"
console = Console(color_system="truecolor")
rh = RichHandler(level = logging.WARNING, console=console)
rh.setFormatter(logging.Formatter(FORMAT_RICH))

#Set up basic config for logger
logging.basicConfig(
	level=logging.INFO, 
	format=FORMAT,
	datefmt="[%X]",
	handlers=[
		rh,
		# logging.FileHandler(f"./data/logs/{current_date}.log", mode="w")
	]
)
logger = logging.getLogger(__name__) 

CONF_DICT={
	"neurips":{
		"name":"Conference and Workshop on Neural Information Processing Systems",
		"abbrv":"NEURIPS",
		"url":"https://neurips.cc/static/virtual/data/neurips-2023-orals-posters.json",
		"headers":{
			"authority":"https://neurips.cc/static/virtual/data/neurips-2023-orals-posters.json",
			"method":"GET",
			"path":"/static/virtual/data/neurips-2023-orals-posters.json",
			"scheme":"https",
			"accept":"*/*",
			"accept-encoding":"gzip,deflate,br,zstd",
			"accept-language":"en-US,en;q=0.9",
			"referer":"https://neurips.cc/virtual/2023/papers.html?filter=titles",
			"sec-ch-ua":'"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
			"sec-ch-ua-Mobile":"?0",
			"sec-ch-ua-platform":"Windows",
			"sec-fetch-dest":"empty",
			"sec-fetch-mode":"cors",
			"sec-fetch-site":"same-origin",
			"user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
			"x-requested-with":"XMLHttpRequest"
			}
	},
	"icml":{
		"name":"International Conference of Machine Learning",
		"abbrv":"ICML",
		"url":"https://icml.cc/static/virtual/data/icml-2023-orals-posters.json",
		"headers":{
			"authority":"https://icml.cc/static/virtual/data/icml-2023-orals-posters.json",
			"method":"GET",
			"path":"/static/virtual/data/neurips-2023-orals-posters.json",
			"scheme":"https",
			"accept":"*/*",
			"accept-encoding":"gzip,deflate,br,zstd",
			"accept-language":"en-US,en;q=0.9",
			"referer":"https://icml.cc/virtual/2023/papers.html?filter=titles",
			"sec-ch-ua":'"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
			"sec-ch-ua-Mobile":"?0",
			"sec-ch-ua-platform":"Windows",
			"sec-fetch-dest":"empty",
			"sec-fetch-mode":"cors",
			"sec-fetch-site":"same-origin",
			"user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
			"x-requested-with":"XMLHttpRequest"
			}
	},
	"ml4h":{
		"name":"Machine Learning for Health",
		"abbrv":"ML4H",
		"url":"stuff",
		"headers":"morestuff"
	}
}

#Will need URL and a dict to store each request header
#FUNCTION log time
def log_time(fn):
	def inner(*args, **kwargs):
		tnow = time.time()
		out = fn(*args, **kwargs)
		te = time.time()
		took = round(te - tnow, 2)
		if took <= 60:
			logging.info(f"{fn.__name__} ran in {took:.2f}s")
		elif took <= 3600:
			logging.info(f"{fn.__name__} ran in {(took)/60:.2f}m")		
		else:
			logging.info(f"{fn.__name__} ran in {(took)/3600:.2f}h")
		return out
	return inner

#FUNCTION Filter result
def extract_json(json_data:json)->dict:
	# Possible cool data within neuripps
	ids = list(range(json_data["count"]))
	base_keys = ["id","name","author","abstract","topic","session","event_type","virtualsite_url","url","paper_url"]
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
			if json_data["results"][id].get(term):
				base_dict[id][term] = json_data["results"][id][term]
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

#FUNCTION save results
def save_result(name:str, processed:pd.DataFrame):
	"""Save Routine.  Takes in name of file and processed dataframe.  Saves it to the data/cleaned folder.  Also offloads the updated CM_dict and PCS_dict variables to JSON for future use. 

	Args:
		name (str): Name of file being converted
		processed (pd.DataFrame): Processed dataframe of translated codes
	"""	
	spath = f"./data/cleaned/web/{name}"
	processed.to_csv(spath, mode='w', header=0, encoding='utf-8')
	logger.info(f"CSV for file {spath} saved")

#FUNCTION save dictionary
def save_data(data):
	result_json = json.dumps(data, indent=4)
	with open(f"./data/json/{data}.json", "w") as outf:
		outf.write(result_json)
	logger.info("data saved")


#NOTE START PROGRAM
#FUNCTION main
@log_time
def main():
	"""Main driver code for program
	"""	
	logger.info(f"Beginning search")
	main_conferences = ["icml", "neurips"]# ,"ml4h"] 
	#TODO - 
		#Add MHSRS when ready, that website will be more challenging to scrape
		#Add ML4H.  
			#Go here to scrape other conferences. 
			#https://proceedings.mlr.press/
	
	for conference in main_conferences[:2]:
		result = request_conf(conference)
		# add_tovectordb(result)
		# save Dataframes
		# save_result(name, processed)
		logger.warning(f"{conference} has been converted and saved")

			#Ryan idea's for embedding
			# Bert embed
			# tsne
			# plot first two components. 
		
	# save_data()		
	logger.warning(f'All conferences have been searched.  Shutting down program')

if __name__ == "__main__":
	main()

