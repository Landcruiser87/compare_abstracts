#main libraries
import datetime
import time
import logging
import os
import json
from rich import print
from rich.tree import Tree
from rich.text import Text
from rich.markup import escape
from rich.filesize import decimal
from rich.console import Console
from rich.logging import RichHandler
from pathlib import Path, PurePath

################################# Logger functions ####################################
#FUNCTION Logging Futures
def get_file_handler(log_dir:Path)->logging.FileHandler:
    """Assigns the saved file logger format and location to be saved

    Args:
        log_dir (Path): Path to where you want the log saved

    Returns:
        filehandler(handler): This will handle the logger's format and file management
    """	
    log_format = "%(asctime)s|%(levelname)-8s|%(lineno)-4d|%(funcName)-13s|%(message)-108s|" 
                 #f"%(asctime)s - [%(levelname)s] - (%(funcName)s(%(lineno)d)) - %(message)s"
    # current_date = time.strftime("%m_%d_%Y")
    file_handler = logging.FileHandler(log_dir)
    file_handler.setFormatter(logging.Formatter(log_format, "%m-%d-%Y %H:%M:%S"))
    return file_handler

def get_rich_handler(console:Console)-> RichHandler:
    """Assigns the rich format that prints out to your terminal

    Args:
        console (Console): Reference to your terminal

    Returns:
        rh(RichHandler): This will format your terminal output
    """
    rich_format = "|%(funcName)-13s| %(message)s"
    rh = RichHandler(console=console)
    rh.setFormatter(logging.Formatter(rich_format))
    return rh

def get_logger(console:Console, log_dir:Path)->logging.Logger:
    """Loads logger instance.  When given a path and access to the terminal output.  The logger will save a log of all records, as well as print it out to your terminal. Propogate set to False assigns all captured log messages to both handlers.

    Args:
        log_dir (Path): Path you want the logs saved
        console (Console): Reference to your terminal

    Returns:
        logger: Returns custom logger object.  Info level reporting with a file handler and rich handler to properly terminal print
    """	
    #Load logger and set basic level
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    #Load file handler for how to format the log file.
    file_handler = get_file_handler(log_dir)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    #Load rich handler for how to display the log in the console
    rich_handler = get_rich_handler(console)
    rich_handler.setLevel(logging.INFO)
    logger.addHandler(rich_handler)
    logger.propagate = False
    return logger

#FUNCTION timer
################################# Timing Funcs ####################################
def log_time(fn):
    """Decorator timing function.  Accepts any function and returns a logging
    statement with the amount of time it took to run. DJ, I use this code everywhere still.  Thank you bud!

    Args:
        fn (function): Input function you want to time
    """	
    def inner(*args, **kwargs):
        tnow = time.time()
        out = fn(*args, **kwargs)
        te = time.time()
        took = round(te - tnow, 2)
        if took <= 60:
            logging.info(f"{fn.__name__} ran in {took:.3f}s")
        elif took <= 3600:
            logging.info(f"{fn.__name__} ran in {(took)/60:.3f}m")		
        else:
            logging.info(f"{fn.__name__} ran in {(took)/3600:.3f}h")
        return out
    return inner

#FUNCTION get time
def get_time():
    """Function for getting current time

    Returns:
        t_adjusted (str): String of current time
    """
    current_t_s = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    current_t = datetime.datetime.strptime(current_t_s, "%m-%d-%Y-%H-%M-%S")
    return current_t
########################## Saving funcs ##########################################
# #FUNCTION save results
# def save_result(name:str, processed:pd.DataFrame, logger:logging):
#     """Save Routine.  Takes in name of file and processed dataframe.  Saves it to the data/cleaned folder. 

#     Args:
#         name (str): Name of file being converted
#         processed (pd.DataFrame): Processed dataframe of translated codes
#     """	
#     spath = f"./data/cleaned/{name}"
#     processed.to_csv(spath, mode='w', header=0, encoding='utf-8')
#     logger.info(f"CSV for file {spath} saved")

################################# Size Funcs ############################################

def sizeofobject(folder)->str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(folder) < 1024:
            return f"{folder:4.1f} {unit}"
        folder /= 1024.0
    return f"{folder:.1f} PB"

def getfoldersize(folder:Path):
    fsize = 0
    for root, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(folder,f)
            fsize += os.stat(fp).st_size

    return sizeofobject(fsize)

def getpapercount(file:Path):
    with open(file, "r") as jfile:
        jfile = json.loads(jfile.read())
        numpapers = len(jfile.keys())

    return numpapers

################################# TUI Funcs ############################################

#FUNCTION Launch TUI
def launch_tui():
    try:
        directory = PurePath(Path.cwd(), Path("./data/conferences/"))

    except IndexError:
        logger.info("[b]Usage:[/] python tree.py <DIRECTORY>")
    else:
        tree = Tree(
            f":open_file_folder: [link file://{directory}]{directory}",
            guide_style="bold bright_blue",
        )
        files = walk_directory(Path(directory), tree)
        print(tree)
    # logger.info(f"There are {pcount} papers in {directory}")
    question ="What file would you like to load?\n"
    file_choice = 28 #console.input(f"{question}")
    if isinstance(file_choice, int):
        file_to_load = files[int(file_choice) - 1]
        #check output directory exists
        return file_to_load
    elif file_choice is None:
        return None

    else:
        raise ValueError("Please restart and select an integer of the file you'd like to import")
    
#FUNCTION Walk Directory
def walk_directory(directory: Path, tree: Tree) -> None:
    """Build a Tree with directory contents.
    Source Code: https://github.com/Textualize/rich/blob/master/examples/tree.py

    """
    # Sort dirs first then by filename
    paths = sorted(
        Path(directory).iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
    )
    idx = 1
    # paper_count = 0
    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        # Just list the CAM folders
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            file_size = getfoldersize(path)
            branch = tree.add(
                f"[bold green]{idx} [/bold green][bold magenta]:open_file_folder: [link file://{path}]{escape(path.name)}[/bold magenta] [bold blue]{file_size}[/bold blue]",
                style=style,
                guide_style=style,
            )
            
            # walk_directory(path, branch)
        else:
            # paper_count += getpapercount(path)
            text_filename = Text(path.name, "green")
            text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            if path.name.split(".")[0].split("_")[1] in MAIN_CONFERENCES:
                icon = "🔥 "
            elif path.name.split(".")[0].split("_")[1] in SUB_CONFERENCES:
                icon = "🐍 "
            elif path.suffix == ".mib":
                icon = "👽 "
            else:
                icon = "🔫 "
            tree.add(Text(f'{idx} ', "blue") + Text(icon) + text_filename)
        idx += 1

    return paths#, paper_count

def list_datasets(paths:list) -> list[tuple]:
    """Main function is list available datasources

    Args:
        paths list[Path]: List of pathlib Path's

    Returns:
        results list[tuple]: Returns a list of file names with their index as tuples
    """

    results = []
    paths = [Path("./data/conferences/"), Path("./data/search_results/")]
    for directory in paths:
        paths = sorted(
            directory.iterdir(),
            key=lambda path: (path.is_file(), path.name.lower()),
        )
        paths = [(val.stem, idx) for idx, val in enumerate(paths)]
        results.extend(paths)
    
    return results


########################## Global Variables to return ##########################################

MAIN_CONFERENCES  = ["ICML", "ICLR", "NEURIPS"]
SUB_CONFERENCES   =  ["COLT", "AISTATS", "AAAI", "CHIL", "ML4H", "ECCV"] #"CLDD"-Got an xml error for 2024

date_json = get_time().strftime("%m-%d-%Y_%H-%M-%S")
console = Console(color_system="auto", stderr=True)
logger = get_logger(console, log_dir=f"data/logs/tui/{date_json}.log") 
