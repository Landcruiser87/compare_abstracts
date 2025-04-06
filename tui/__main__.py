from __future__ import annotations

import argparse
import logging
import platform
import sys
from support import logger
import support

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

from __init__ import PaperSearch, __prog_name__, __version__

WINDOWS = platform.system() == "Windows"
DEBUGPY_PORT = 5678

def main():
    parser = argparse.ArgumentParser(
        prog=__prog_name__, description="Json Tree - ML Conference", epilog=f"v{__version__}"
    )

    parser.add_argument(
        "-V",
        "--version",
        help="Show version information.",
        action="version",
        version=f"%(prog)s {__version__} (Textual v{importlib_metadata.version( 'textual' )})",
    )

    parser.add_argument(
        "--log", nargs="?", help="Log level for enable debugpy", default="INFO"
    )

    parser.add_argument(
        "path",
        nargs="?",
        type=argparse.FileType(encoding="utf-8", mode="r"),
        metavar="PATH",
        help="path to file, or stdin",
        default=sys.stdin,
    )

    args = parser.parse_args()
    numeric_level = getattr(logging, args.log.upper(), None)
    file_choice = ""
    if not isinstance(numeric_level, int):
        logger.warning(f"Invalid log level {args.log!r}")
    
    # Check if no path was provided as a command-line argument
    if args.path is sys.stdin:
        file_choice = support.launch_tui()
    
    # If a file was chosen
    if file_choice:
        try:
            # Open the file chosen by the TUI
            args.path = open(file_choice, mode="r", encoding="utf-8")
        except FileNotFoundError:
            logger.error(f"File not found: {file_choice}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error opening file {file_choice}: {e}")
            sys.exit(1)

    # if numeric_level == logging.DEBUG:
    #     import debugpy
    #     debugpy.listen(DEBUGPY_PORT)
    #     debugpy.wait_for_client()
    
    try:
        # See:Textualize/textual/issues/153#issuecomment-1256933121
        if not WINDOWS:
            sys.stdin = open("/dev/tty", "r")
        
        app = PaperSearch(args.path)
        app.run()

        if not sys.stdin.closed:
            sys.stdin.close()

    except Exception as error:
        logger.warning(f"Unable to read {args.path!r}; {error}")
        sys.exit(-1)

if __name__ == "__main__":
    main()

#IDEA
#Grab all of above
#Need a better way to search. 
    #maybe think of filtering like Zotero?
    #NoSQL won't really be available...  
    #could parse the topic field

        #partially done in the explore.py
    #year filtering
    #Add multiple conf
    #load all function. 
    #TODO - similarity search from a selected paper. 
        #Within conference?  
            #Main goal is to pull back the top 10 similar papers
            #Make this a keybinding when you search on the abstract. 
            #shift f.
            #Behavior is add another node on the root tree (toggle to root or something)
                #Add the node as the next node.
                #Or fill out a tab in the other side with... another tree node?
                #You'll want to read the other papers right. soooo.  
                
        #Against other conferences?
    #TODO - 
    #IDEA Institution frequency graph
        #Separate metrics for ICML, ICLR AND neurips as they have way more info.  And the 
        #only one's I can identify university.   DOH!
    #IDEA hieracrhy research of common cited sources!!! Create knowledge graph of similar sourcing. 
    #IDEA google scholar ?  hindex and impact scores???
    #IDEA Send selected file from JSON to Zotero

#Layout
#1. Sidebar popout that controls each page.  
    #Select year tree?
    #Select conf dropdown?
    #Select similarity measure?
#2. Activate new source item (left pane) when 


##########  V 0.3.0 ###############################
#Updated workflow
# 1. Load up app traditional way.
    # Select number of conf you want to load.  
        # ?Maybe add an option for all... 
        #? Or maybe!!! you could submit a list of ID's load as tree nodes / roots.  Search for if comma's are in the string, split it and iterate the loop
            #winner winner chicken dinner
# 2. First panels up will be the jsontree (left) and regular results conainter but as the first tab of of a tabbed content widget. 
# 3a. You can navigate normally and arrow through the json tree
# 3b. Or click the search to allow for saerches
# 4.  Add or remove datasets 


###########  Tabbed Content ##########################
# Dataset Tab
# When you load the tab (which should be when on_mount creates the object), 
# on_mount
    #Load all the available datasets in the data/conferences folder
    #into the checklist widget
# You have two buttons to the left.  One that add's datasets, one that removes them.  
    # For that function, have it cycle through the checklist box and grab the enabled 
    # triggers.  (like the gpu_monitor) 

#Search Tab
#Logic here will be more complex.  
#Idea is i want a search box to type in queries
#I want to be able to select what field i want to search. 
#And also select what metric I want to use for comparison and search.
#Probably need an input box too for limiting results. 

#When a comparison run is made. 
#Add that node to the root node with the other datasets.  
#Also, save it to a separate data folder to allow for exploration later or a compairs of results
    #This means i'll have to update the loader function to look across both
    #folders, but that too can be something you select at the beginning just
    #with another file listing of the two folders

#!ISSUE
    #How do you handle conferences that don't have certain fields filled out?
    #abstraact and title are pretty good...  
    #authors would be fun, but I have no idea what will look like.
    #
    #!Do i want to be maninpulating the underlying datasets?....probably not
        # Ways to pull that info
        #1. Zotero connection.  Have it run through pyzotero and grab the extra info
        #2. Basic google scholar search?
        #3. ORCID search?
        #I'm not sure i can be doing this, but save this for the next iteration. 
    #title/abstract is really the only field that is always filled out.    