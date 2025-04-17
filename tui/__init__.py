from __future__ import annotations
#Main imports
import json
import sys
import asyncio
import numpy as np
from time import sleep
from typing import TYPE_CHECKING, Optional
from pathlib import Path, PurePath
from collections import deque

#Textual Imports
from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.reactive import reactive, var
from widgets import (
    JSONDocumentView, 
    JSONTree, 
    TreeView, 
    LoadingIndicator,
    SearchProgress
) 
from textual.containers import Container, Horizontal, Vertical
from textual.fuzzy import Matcher
from textual.widgets import (
    Button, 
    Footer,
    Header,
    Input,
    Static,
    SelectionList,
    RadioButton, 
    RadioSet,
    TabbedContent, 
    TabPane,       
    Tree
)
from textual.widgets.selection_list import Selection
#Custom Imports
from utils import clean_string_values, get_c_time, cosine_similarity, clean_vectorize
from support import list_datasets, save_data, SEARCH_FIELDS, SEARCH_METRICS

if TYPE_CHECKING:
    from io import TextIOWrapper

__prog_name__ = "ML_Jtree"
__version__ = "0.3.0"

#CLASS - Load Data
class PaperSearch(App):
    TITLE = __prog_name__
    SUB_TITLE = f"A JSON exploration tool for influential Machine Learning Papers ({__version__})"
    CSS_PATH = "css/layout.tcss"
    BINDINGS = [
        ("ctrl+s", "app.screenshot()", "Screenshot"),
        ("ctrl+t", "toggle_root", "Toggle root"),
        ("enter", "display_selected", "Display Selected"),  
        Binding("q", "app.quit", "Quit"),
    ]
    
    json_name: str = ""
    json_data: reactive[str] = reactive("")
    root_data_dir = var(Path("./data/conferences"))
    srch_data_dir = var(Path("./data/searches"))
    selected_node_data:  reactive[object | None] = reactive(None)
    all_datasets: list = list_datasets()

    def __init__(
        self,
        json_file: TextIOWrapper,
        driver_class=None,
        css_path=None,
        watch_css=False,
    ):
        super().__init__(driver_class, css_path, watch_css)

        if json_file is sys.stdin:
            self.json_data = "".join(sys.stdin.readlines())
        else:
            self.json_data = json_file.read()
            json_file.close()

        if "/" in json_file.name:
            self.json_name = json_file.name.split("/")[-1]
        elif "\\" in json_file.name:
            self.json_name = json_file.name.split("\\")[-1]

    #FUNCTION - Load Data
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container(id="app-grid"):
            # Left side - JSON Tree
            yield TreeView(id="tree-container")
            # Right side - Tabbed Content
            with TabbedContent(id="tab-container", initial="content-tab"):
                # Tab 1 - Document View
                with TabPane("Document", id="content-tab"):
                    yield JSONDocumentView(id="json-document-view")
                # Tab 2 - Search (Placeholder)
                with TabPane("Search", id="search-tab"):
                    with Container(id="srch-container"):
                        yield Input("Type search here", id="input-search")
                        yield Static("Search Metrics", id="hdr-metric", classes="header")
                        yield Static("Search Field", id="hdr-field", classes="header")
                        yield Static("Search Params", id="hdr-param", classes="header")
                        
                        with RadioSet(id="radio-metrics", classes="header"):
                            for metric in SEARCH_METRICS:
                                yield RadioButton(metric)
                        with RadioSet(id="radio-fields", classes="header"):
                            for field in SEARCH_FIELDS:
                                yield RadioButton(field)
                        with Container(id="sub-container"):
                            with Vertical(id="srch-fields"):
                                yield Input("res limit", tooltip="Limit the amount of returned results", id="input-limit", type="integer")
                                yield Input("threshold", tooltip="Threshold the appropriate metric", id="input-thres", type="number")
                            yield Button("Search Datasets", id="search-button")
                # Tab 3 - Manage Datasets - Buttons and SelectionList
                with TabPane("Manage Datasets", id="manage-tab"):
                    with Horizontal(id="dataset-container"):
                        with Container(id="dc-leftside"):
                            yield Static("Available Datasets", id="data-title", classes="header")
                            yield SelectionList(*self.all_datasets, name="Dataset List", id="datasets")

                        with Container(id="dc-rightside"):
                            yield Button("Add Dataset", id="add-button")
                            yield Button("Remove Dataset", id="rem-button")

        yield Footer()

    #FUNCTION - onmount
    def on_mount(self) -> None:
        tree_view = self.query_one(TreeView)
        tree = tree_view.query_one(JSONTree)
        root_name = self.json_name
        if root_name:
            json_data = self.load_data(tree, root_name, self.json_data)
        json_docview = self.query_one(JSONDocumentView)
        json_docview.update_document(json_data)
        tree.focus()

    #FUNCTION - Load Data
    def load_data(self, json_tree: TreeView, root_name:str, json_data:dict|str) -> dict:
        new_node = json_tree.root.add(root_name)
        if isinstance(json_data, str):
            json_data = clean_string_values(json.loads(json_data))
            json_tree.add_node(root_name, new_node, json_data)
        elif isinstance(json_data, dict):
            json_data = clean_string_values(json_data)
            json_tree.add_node(root_name+".json", new_node, json_data)
        return json_data
    
    def add_datasets(self, tree:Tree, datasets:SelectionList, selected:list, loading:LoadingIndicator) -> None:
        def has_numbers(inputstring):
            return any(char.isdigit() for char in inputstring)

        for itemid in selected:
            #BS way to get around list index errors for last selected item
            # if itemid == len(datasets.options):
            #     itemid -= 1
            new_json = datasets.options[itemid].prompt._text[0] + ".json"
            loading.message = f"Loading {new_json}"
            loading.update()
            if has_numbers(new_json):
                source_p = self.root_data_dir
            else:
                source_p = self.srch_data_dir
            json_path = PurePath(Path.cwd(), source_p, Path(new_json))
            json_data = open(json_path, mode="r", encoding="utf-8").read()
            self.load_data(tree, new_json, json_data)
            loading.count += 1
            loading.update_progress(loading.count, len(selected))
            self.notify(f"{new_json} loaded")
            sleep(0.5)

    #FUNCTION - Remove Data
    def remove_datasets(self, tree:Tree, datasets:SelectionList, selected:list, loading:LoadingIndicator) -> None:
        for itemid in selected:
            #BUG here when removing custom searches.  
            #BS way to get around list index errors for last selected item
            # if itemid == len(datasets.options):
            #     itemid -= 1
            rem_conf = datasets.options[itemid].prompt._text[0] + ".json"
            loading.message = f"Removing {rem_conf}"
            loading.update()
            for node in tree.root.children:
                if rem_conf in node.label.plain:
                    node.remove()
                    self.notify(f"{rem_conf} removed")
            loading.count += 1
            loading.update_progress(loading.count, len(selected))
            sleep(0.5)

    #FUNCTION - run search
    def run_search(self, tree:Tree, loading:LoadingIndicator) -> None:

        def is_numeric_string(s: str) -> bool:
            """
            Checks if a string represents a valid integer or float.

            Handles integers, floats, scientific notation, and leading/trailing whitespace.
            Note: Also returns True for 'inf', '-inf', and 'nan'.

            Args:
                s: The string to check.

            Returns:
                True if the string can be converted to a float, False otherwise.
            """
            if not isinstance(s, str):
                return False # Ensure input is a string
            try:
                float(s)
                return True
            except ValueError:
                return False
            except TypeError: 
                return False
            
        #FUNCTION - launch cos sim
        def launch_cos(srch_txt:str, srch_field:str, node:Tree):
            tfid, paper_names = clean_vectorize(srch_txt, srch_field, node)
            sims = cosine_similarity(tfid, "scipy")
            return sims[1:], paper_names[1:]

        #FUNCTION conf search
        def conf_search(
                srch_text:str, 
                node:Tree, 
                variables:list,
                conf:str
            ):
            #Load variables
            results = {}
            metric = SEARCH_METRICS[variables[0]]
            field = SEARCH_FIELDS[variables[1]]
            res_limit = int(variables[2])
            threshold = float(variables[3])
            #Decide metric
            if metric == "Fuzzy":
                node_queue = deque(node.children)
                while node_queue:
                    paperkey = node_queue.popleft()
                    labels = [x.label.plain.split("=")[0] for x in paperkey.children]                 
                    if field in labels:
                        index = labels.index(field)
                        criteria = paperkey.children[index].label.plain.split("=")[1]
                        query = Matcher(srch_text)
                        match_num = query.match(criteria)
                        if match_num > threshold:
                            reskey = paperkey.label.plain[3:]
                            results[reskey] = paperkey.data
                            results[reskey]["metric_match"] = round(match_num, 3)
                            results[reskey]["metric_thres"] = threshold
                            results[reskey]["conference"] = conf

            elif metric == "Cosine":
                sims, paper_names = launch_cos(srch_text, field, node) #return matchnum too
                arr = np.array(sims, dtype=np.float32)
                qual_indexes = np.where(arr >= threshold)[0]
                if qual_indexes.shape[0] > 0:
                                   #Index,paper_name,     sim)
                    paper_info = [(idx, paper_names[idx], arr[idx]) for idx in qual_indexes]
                    node_queue = deque(node.children)
                    while node_queue:
                        paperkey = node_queue.popleft()
                        label = paperkey.label.plain.strip("{}").strip()
                        papers = [x[1] for x in paper_info]
                        if label in papers:
                            labels = [x.label.plain.split("=")[0] for x in paperkey.children]                 
                            if field in labels:
                                index = labels.index(field)
                                results[label] = paperkey.data
                                similarity = paper_info[papers.index(label)][2].item()
                                results[label]["metric_match"] = round(similarity, 4)
                                results[label]["metric_thres"] = threshold
                                results[label]["conference"] = conf


            elif metric == "Levenstein":
                self.notify(f"{metric} search currently not available")
            elif metric == "Hamming":
                self.notify(f"{metric} search currently not available")
            elif metric == "Jaccard":
                self.notify(f"{metric} search currently not available")
            elif metric == "LCS":
                self.notify(f"{metric} search currently not available")
            
            res = sorted(results.items(), key=lambda x:x[1].get("metric_match"), reverse=True)[:res_limit]
            return dict(res)

        srch_text = self.query_one("#input-search", Input).value
        metric = self.query_one("#radio-metrics", RadioSet)._reactive__selected
        field = self.query_one("#radio-fields", RadioSet)._reactive__selected
        res_limit = self.query_one("#input-limit", Input).value
        threshold = self.query_one("#input-thres", Input).value
        variables = [metric, field, res_limit, threshold]
        if not all(is_numeric_string(str(var)) for var in variables):
            self.notify("Search inputs are malformed.\nCheck inputs (int or float) and try again")
            return 

        root_name = f"{SEARCH_METRICS[metric].lower()}_{SEARCH_FIELDS[field]}_{'-'.join(srch_text.lower().split())}"
        results = {}
        loading.render()
        for node in tree.root.children:
            conf = node.label.plain.split()[1]
            self.notify(f"Searching {conf}")
            result = conf_search(srch_text, node, variables, conf)
            if result:
                results.update(**result)
            else:
                self.notify(f"No results found in {conf}")
            loading.advance(1)
            sleep(0.5)

        if results:
            self.load_data(tree, root_name, results)
            save_data(root_name, results)
            self.notify(f"{len(results.keys())} found in {conf}")

        else:
            self.notify("No results found in all datasets")
            sleep(2)

    #FUNCTION Tree Node select
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node in the tree is selected."""
        self.selected_node_data = event.node.data
    
    #FUNCTION Button press event
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when a button is pressed."""
        #Get references to necessary widgets / data
        button_id = event.button.id
        tree_view = self.query_one(TreeView)
        tree = tree_view.query_one(JSONTree)
        datasets = self.query_one(SelectionList)
        selected = datasets.selected

        #Progress bar loading
        loading_container = Container(id="loading-container")
        if button_id != "search-button":
            loading = LoadingIndicator()
        else:
            loading = SearchProgress(total=len(tree.root.children), count=0)
        self.mount(loading_container)
        loading_container.mount(loading)
        #BUG- Index Error
            #I think... i'm getting this error because i'm not reloading the 
            #SelectionList with all available datasets?
            #Think about implementing an update func to the list

        #FUNCTION Async data task
        async def manage_data_task():
            if button_id == "add-button":
                self.add_datasets(tree, datasets, selected, loading)
                await asyncio.sleep(0.1)
            elif button_id == "rem-button":
                self.remove_datasets(tree, datasets, selected, loading)
                await asyncio.sleep(0.1)
            elif button_id == "search-button":
                self.run_search(tree, loading) 
                await asyncio.sleep(0.1)
            
            #Manually refresh SelectionList options to avoid index errors
            datasets.clear_options()
            self.all_datasets = list_datasets()
            new_datasets = [
                Selection(s[0], s[1], False)
                for s in self.all_datasets
            ]
            datasets.add_options(new_datasets)
            loading_container.remove()
        
        self.run_worker(manage_data_task, thread=True)

    #FUNCTION watch data node
    def watch_selected_node_data(self, new_data: object | None) -> None:
        """Watches for changes to selected_node_data and updates the display."""
        json_docview = self.query_one(JSONDocumentView)

        if new_data is not None:
            if isinstance(new_data, (dict, list, str, int)):
                json_docview.update_document(new_data)
        else:
             json_docview.update_document("")
        
        activetab = self.query_one(TabbedContent)
        tree = self.query_one(TreeView)
        if not activetab.active == "content-tab" :
            tree_view = self.query_one(TreeView)
            tree = tree_view.query_one(JSONTree)
            json_docview.focus()
            tree.focus()

    #FUNCTION Screenshot
    def action_screenshot(self):
        current_time = get_c_time()
        self.save_screenshot(f"{current_time}.svg", "./data/screenshots/" )
    
    #FUNCTION toggle root
    def action_toggle_root(self) -> None:
        tree = self.query_one(JSONTree)
        tree.show_root = not tree.show_root


#TODO - Add Clustering tab to results.  

    #First idea is to add the search as a new json to the treeview
    #label it with date and search keywords.  
        #?Not sure how to store the selected datasets at the time. 
        #Maybe i can do it as a global
    #look at venvkiller for how he did that. probalby a custom class

#Search workflow. 
#- When you select a search field. 
    #Other fields in the search metrics will enable/disable
#- That way you won't have unmapped search paths

#Possible Search paths
#1. Basic text match searching.  
    #This can be run with the following

