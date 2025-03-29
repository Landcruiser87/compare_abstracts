from os.path import exists
import json

def main():
    years = range(2021, 2022)
    conferences = ["AISTATS", "COLT", "ML4H", "CHIL"]
    for year in years:
        for conf in conferences:
            fp = str(year) + "_" + conf + ".json"
            if exists(fp):
                with open(fp, "r") as f:
                    fixme = json.loads(f.read())
                    for key, val in fixme.items():
                        fixme[key] = val

                        
if __name__ == "__main__":
    main()
