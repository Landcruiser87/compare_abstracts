import numpy as np
import pandas as pd
from rich.logging import RichHandler
from rich.console import Console
from time import strftime, sleep
from collections import Counter
from itertools import chain
import os
import logging
import json
import time

papers_dict, all_dict = {}, {}
for year in [2021, 2022, 2023]:
	for conference in ["neurips", "icml"]:
		with open(f"../data/scraped/{year}_{conference}.json", "r") as f:
			papers_dict = json.loads(f.read())
			# remap the keys so they don't overlap
			papers_dict = {k+f"_{conference[:1]}_{str(year)[-2:]}":v for k, v in papers_dict.items()}
			all_dict.update(**papers_dict)

#lets.... look at keywords first. 
keywords = [all_dict[x]["keywords"] for x in list(all_dict.keys())]
c_keys = Counter(list(chain(*keywords)))
res_dict = dict(c_keys)
sorted(c_keys.items(), key=lambda x:x[1], reverse=True)[:10]

topics = [all_dict[x]["topic"] for x in list(all_dict.keys())]
c_topics = Counter(topics)
res_dict.update(**c_topics)
sorted(c_topics.items(), key=lambda x:x[1], reverse=True)[:10]

sorted(res_dict.items(), key=lambda x:x[1], reverse=True)[:10]

#now research centers 
centers = [[all_dict[x]["author"][auth]["institution"] for auth in all_dict[x]["author"].keys()] for x in list(all_dict.keys())]
counts = Counter(list(chain(*centers)))
counts = sorted(counts.items(), key=lambda x:x[1], reverse=True)

#Justins idea
#NLP stuffs

#embed it and ... do stuff?
