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

for YEAR in [2021, 2022, 2023]:
	for CONFERENCE in ["neurips", "icml"]:
		with open(f"../data/scraped/{YEAR}_{CONFERENCE}.json", "r") as f:
			papers_dict = json.loads(f.read())
			papers_dict = {k+f"_{CONFERENCE[:1]}_{str(YEAR)[-2:]}":v for k, v in papers_dict.items()}
			all_dict.update(papers_dict)
			
#lets.... look at topics first. 
topics = [papers_dict[x]["topic"] for x in list(papers_dict.keys())]
c_topic = Counter(topics)
sorted(c_topic.items(), key=lambda x:x[1], reverse=True)

#now research centers
centers = [[papers_dict[x]["author"][auth]["institution"] for auth in papers_dict[x]["author"].keys()] for x in list(papers_dict.keys())]
counts = Counter(list(chain(*centers)))
counts = sorted(counts.items(), key=lambda x:x[1], reverse=True)