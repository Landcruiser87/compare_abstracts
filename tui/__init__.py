from __future__ import annotations
#Main imports
import json
import sys
import asyncio
from time import sleep
from typing import TYPE_CHECKING, Optional
from pathlib import Path, PurePath
from collections import deque
#Textual Imports
from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.reactive import reactive, var
from widgets import JSONDocumentView, JSONTree, TreeView, LoadingIndicator
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

#Custom Imports
from utils import clean_string_values, get_c_time, cosine_similarity, clean_vectorize
from support import list_datasets, save_data, SEARCH_KEYS, SEARCH_METRICS

if TYPE_CHECKING:
    from io import TextIOWrapper

__prog_name__ = "ML_Jtree"
__version__ = "0.3.0"

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
                            for field in SEARCH_METRICS:
                                yield RadioButton(field)
                        with RadioSet(id="radio-fields", classes="header"):
                            for field in SEARCH_KEYS:
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
    
    def add_datasets(self, tree:Tree, datasets:SelectionList, selected:list, loading:LoadingIndicator) -> None:
        def has_numbers(inputstring):
            return any(char.isdigit() for char in inputstring)

        for itemid in selected:
            new_json = datasets.options[itemid].prompt._text[0] + ".json"
            loading.message = f"Loading {new_json}"
            if has_numbers(new_json):
                source_p = self.root_data_dir
            else:
                source_p = self.srch_data_dir
            json_path = PurePath(Path.cwd(), source_p, Path(new_json))
            json_data = open(json_path, mode="r", encoding="utf-8").read()
            self.load_data(tree, new_json, json_data)
            sleep(1)
            loading.count += 1
            loading.update_progress(loading.count, len(selected))

    def remove_datasets(self, tree:Tree, datasets:SelectionList, selected:list, loading:LoadingIndicator) -> None:
        for itemid in selected:
            rem_conf = datasets.options[itemid].prompt._text[0] + ".json"
            loading.message = f"Removing {rem_conf}"
            for node in tree.root.children:
                if rem_conf in node._label:
                    node.remove()
            loading.count += 1
            loading.update_progress(loading.count, len(selected))
            sleep(0.2)

    def run_search(self, tree:Tree, datasets:SelectionList, selected:list, loading:LoadingIndicator) -> None:
            
        # def launch_cos(srch_txt:str, srch_field:str, node):
        #     tfid = clean_vectorize(srch_text, srch_txt, srch_field, node)
        #     sims = cosine_similarity(tfid, "scipy")
        #     return sims#, match_num
        

        def conf_search(srch_text:str, metric:str, field:str, node):
            results = {}
            res_limit = int(self.query_one("#input-limit", Input).value)
            threshold = float(self.query_one("#input-thres", Input).value)
            srch_field = SEARCH_KEYS[field]
            srch_type = SEARCH_METRICS[metric]

            if srch_type =="Fuzzy":
                node_queue = deque(node.children)
                while node_queue:
                    paperkey = node_queue.popleft()
                    labels = [x.label.plain.split("=")[0] for x in paperkey.children]                 
                    if srch_field in labels:
                        index = labels.index(srch_field)
                        criteria = paperkey.children[index].label.plain.split("=")[1]
                        query = Matcher(srch_text)
                        match_num = query.match(criteria)
                        if match_num > threshold:
                            reskey = paperkey.label.plain[3:]
                            results[reskey] = paperkey.data
                            results[reskey]["metric_match"] = round(match_num, 3)
                            results[reskey]["metric_thres"] = threshold

            # elif srch_type =="Cosine Sim":
            #     results = launch_cos(srch_text, srch_field, node) #return matchnum too

            elif srch_type =="Levenstein":
                pass
            elif srch_type =="Hamming":
                pass
            elif srch_type =="Jaccard":
                pass
            elif srch_type == "LCS (Lowest Common Subsquence)":
                pass
            
            res = sorted(results.items(), key=lambda x:x[1].get("metric_match"), reverse=True)[:res_limit]
            return dict(res)

        #Noooooooooooooot sure what to do here. 
        #1. First I need the path of the data i'm searching
        #2. Loop through each record in the JSON. 
        #3. See if search metric is in the keys.
        #4. Run fuzzy matching on all fiels.  
        #5. Return results as new JSON

        srch_text = self.query_one("#input-search", Input).value
        metric = self.query_one("#radio-metrics", RadioSet)._reactive__selected
        field = self.query_one("#radio-fields", RadioSet)._reactive__selected
        root_name = f"{SEARCH_METRICS[metric]}_{SEARCH_KEYS[field]}_{srch_text}"
        results = {}
        for node in tree.root.children:
            conf = node.label.plain.split()[1]
            loading.message = f"Searching {conf}"
            result = conf_search(srch_text, metric, field, node)
            if result:
                results.update(**result)
            else:
                loading.message = f"No results found in {conf}"
            loading.count += 1
            loading.update_progress(loading.count, len(selected))

        if results:
            self.load_data(tree, root_name, results)
            save_data(root_name, results)
        else:
            loading.message = "No results found "


    def on_mount(self) -> None:
        tree_view = self.query_one(TreeView)
        tree = tree_view.query_one(JSONTree)
        root_name = self.json_name
        json_data = self.load_data(tree, root_name, self.json_data)
        json_docview = self.query_one(JSONDocumentView)
        json_docview.update_document(json_data)
        tree.focus()

    def load_data(self, json_tree: TreeView, root_name:str, json_data:dict|str) -> dict:
        new_node = json_tree.root.add(root_name)
        if isinstance(json_data, str):
            json_data = clean_string_values(json.loads(json_data))
        elif isinstance(json_data, dict):
            json_data = clean_string_values(json_data)
        json_tree.add_node(root_name, new_node, json_data)
        return json_data

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node in the tree is selected."""
        self.selected_node_data = event.node.data

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when a button is pressed."""
        #Get references to necessary widgets / data
        button_id = event.button.id
        tree_view = self.query_one(TreeView)
        tree = tree_view.query_one(JSONTree)
        datasets = self.query_one(SelectionList)
        selected = datasets.selected
        loading_container = Container(id="loading-container")
        loading = LoadingIndicator()
        self.mount(loading_container)
        loading_container.mount(loading)

        async def manage_data_task():
            if button_id == "add-button":
                self.add_datasets(tree, datasets, selected, loading)

            elif button_id == "rem-button":
                self.remove_datasets(tree, datasets, selected, loading)

            elif button_id == "search-button":
                self.run_search(tree, datasets, selected, loading)

            loading_container.remove()
        
        self.run_worker(manage_data_task, thread=True)

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

    def action_screenshot(self):
        current_time = get_c_time()
        self.save_screenshot(f"{current_time}.svg", "./data/screenshots/" )

    def action_toggle_root(self) -> None:
        tree = self.query_one(JSONTree)
        tree.show_root = not tree.show_root


#TODO - Add Clustering tab to results.  

#TODO - Figure out search storage. 
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

