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
for year in range(2020, 2025):
    for conference in ["neurips", "icml", "iclr"]:
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

#Research centers with the most papers accepted
centers = [set([all_dict[x]["author"][auth]["institution"] for auth in all_dict[x]["author"].keys()]) for x in list(all_dict.keys())]
centers = [list(x) for x in centers]
count_d = dict(Counter(list(chain(*centers))))

#Combine known repeat centers
tupes = [
    ("Massachusetts Institute of Technology", "MIT"),
     ("Tsinghua University","Tsinghua University, Tsinghua University"),
    ("Stanford University", "Stanford"),
    ("UCLA", "University of California, Los Angeles"),
    ("UC Berkeley", "University of California, Berkeley")
]
for tupe in tupes:
    count_d[tupe[0]] += count_d[tupe[1]]
    del count_d[tupe[1]]
     
counts = sorted(count_d.items(), key=lambda x:x[1], reverse=True)

#get rid of None's (third val)
counts.pop(2)
counts.pop(15)
counts[:40]

#Justins idea
#NLP stuffs
#embed it and ... do stuff?  ehh ok

#Ned Idea
#Take a lookat who's using open source LLM's vs for profit LLM's. 
#Could be an interesting dynamic to look at  to see how much adoption
#of the open source frameworks has occured.



