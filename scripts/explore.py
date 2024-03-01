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


YEAR = 2023
CONFERENCE = "neurips"
with open(f"../data/scraped/{YEAR}_{CONFERENCE}.json", "r") as f:
	conf_dict = json.loads(f.read())
	print(conf_dict.keys())

#lets.... look at topics first. 
topics = [conf_dict[x]["topic"] for x in list(conf_dict.keys())]
c_topic = Counter(topics)
sorted(c_topic.items(), key=lambda x:x[1], reverse=True)

#now research centers
centers = [[conf_dict[x]["author"][auth]["institution"] for auth in conf_dict[x]["author"].keys()] for x in list(conf_dict.keys())]
counts = Counter(list(chain(*centers)))
counts = sorted(counts.items(), key=lambda x:x[1], reverse=True)