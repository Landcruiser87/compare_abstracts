from os.path import exists
from pathlib import Path, PurePath
import support
from support import logger
import json

def main():
    years = range(2021, 2023)
    conferences = ["AISTATS", "COLT", "ML4H", "CHIL"]
    
    for year in years:
        for conf in conferences:
            fp = PurePath(Path.cwd(), Path("data/conferences/" + str(year) + "_" + conf + ".json"))
            if exists(fp):
                temp_dict = {}
                with open(fp, "r") as f:
                    fixme = json.loads(f.read())
                    for key, val in fixme.items():
                        idx = key.index("_")
                        if key[idx + 1] == " ":
                            new_key = key[:idx] + "_" +  key[idx + 2:]
                            temp_dict[new_key] = val
                        else:
                            temp_dict[key] = val
                logger.info(f"{fp} updated")            
                support.save_data(temp_dict, conf, year)
                
if __name__ == "__main__":
    main()
