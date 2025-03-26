#main libraries
import datetime
import time
import json
import logging
from pathlib import Path

#Progress bar fun
from rich.progress import (
    Progress,
    BarColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn
)
from rich.console import Console
from rich.logging import RichHandler

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


########################## Global Variables to return ##########################################

console = Console(color_system="auto", stderr=True)
DATE_JSON = get_time().strftime("%m-%d-%Y_%H-%M-%S")
logger = get_logger(console, log_dir=f"data/logs/scrape/{DATE_JSON}.log") 

########################## Saving funcs ##########################################
#FUNCTION save dictionary
def save_data(data:dict, conference:str, YEAR:int, logger:int):
    # sorted_dict = dict(sorted(jsond.items(), key=lambda x:datetime.datetime.strftime(x[1]["pub_date"], "%Y-%m-%d").split("-"), reverse=True))
    result_json = json.dumps(data, indent=2)
    with open(f"./data/scraped/{YEAR}_{conference}.json", "w") as outf:
        outf.write(result_json)
    logger.info(f"{conference:7s}:{YEAR} data saved")

################################# Rich Spinner Control ####################################

#FUNCTION Progress bar
def mainspinner(console:Console, totalstops:int):
    """Load a rich Progress bar for alerting you to the progress of the search

    Args:
        console (Console): reference to the terminal
        totalstops (int): Amount of years * num of conferences to be searched

    Returns:
        my_progress_bar (Progress): Progress bar for tracking overall progress
        jobtask (int): mainjob id for ecg extraction
    """

    my_progress_bar = Progress(
        TextColumn("{task.description}"),
        SpinnerColumn("aesthetic"),
        BarColumn(),
        TextColumn("*"),
        "time elapsed:",
        TextColumn("*"),
        TimeElapsedColumn(),
        TextColumn("*"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
        console=console,
        refresh_per_second=6,
        redirect_stdout=False
    )
    jobtask = my_progress_bar.add_task("[green] searching papers", total=totalstops + 1)
    return my_progress_bar, jobtask

def add_spin_subt(prog:Progress, msg:str, howmanysleeps:int):
    """Adds a secondary job to the main progress bar

    Args:
        prog (Progress): Main progress bar
        msg (str): Message to update secondary progress bar
        howmanysleeps (int): How long to let the timer sleep
    """
    #Add secondary task to progbar
    liljob = prog.add_task(f"[magenta]{msg}", total = howmanysleeps)
    #Run job for random sleeps
    for _ in range(howmanysleeps):
        time.sleep(1)
        prog.update(liljob, advance=1)
    #Hide secondary progress bar
    prog.update(liljob, visible=False)
