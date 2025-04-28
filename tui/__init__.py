from __future__ import annotations
#Main imports
import json
import sys
import asyncio
import numpy as np
from time import sleep
from typing import TYPE_CHECKING, List, Tuple, Dict, Any 
from pathlib import Path, PurePath
from collections import deque
#Textual Imports
from textual import on, work
from textual.binding import Binding
from textual.app import App, ComposeResult
from widgets import (
    JSONDocumentView, 
    JSONTree,
    TreeView, 
    SearchProgress
) 
from textual.containers import Container, Horizontal, Vertical, Widget
from textual.fuzzy import Matcher
from textual.worker import Worker, get_current_worker
from textual.reactive import reactive, var
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
from support import list_datasets, save_data, SEARCH_FIELDS, SEARCH_METRICS, logger

if TYPE_CHECKING:
    from io import TextIOWrapper

__prog_name__ = "ML_Tree"
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
    json_data: str = ""
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
        tree = tree_view.query_one(Tree)
        root_name = self.json_name
        if root_name:
            json_data = self.load_data(tree, root_name, self.json_data)
        json_docview = self.query_one(JSONDocumentView)
        json_docview.update_document(json_data)
        tree.focus()


    @on(SelectionList.SelectedChanged)
    def on_selection(self, event: SelectionList.SelectedChanged) -> None:
        abutton = self.query_one("#add-button", Button)
        rbutton = self.query_one("#rem-button", Button)
        selections = len(event.selection_list.selected)
        if selections > 0:
            abutton.label = f"Add {selections} datasets"
            rbutton.label = f"Remove {selections} datasets"
        else:
            abutton.label = f"Add Data"
            rbutton.label = f"Remove Data"

    def reload_selectionlist(self, datasets:SelectionList) -> None:
        #Manually refresh SelectionList options to avoid index errors
        datasets.clear_options()
        self.all_datasets = list_datasets()
        new_datasets = [
            Selection(s[0], s[1], False)
            for s in self.all_datasets
        ]
        datasets.add_options(new_datasets)

    @on(Button.Pressed, "#add-button")
    def add_button_event(self):
        self.add_datasets()

    @on(Button.Pressed, "#rem-button")
    def remove_button_event(self):
        self.remove_datasets()

    @on(Button.Pressed, "#search-button")
    def search_button_event(self):
        self.run_search()

    #FUNCTION - Load Data
    def load_data(self, json_tree: TreeView, root_name:str, json_data:dict|str) -> dict:
        if isinstance(json_data, str):
            new_node = json_tree.root.add(root_name)
            json_data = clean_string_values(json.loads(json_data))
            json_tree.add_node(root_name, new_node, json_data)
            return json_data

    def add_datasets(self):
        """Handles the 'Add Dataset' button press by launching a worker."""
        datasets_widget: SelectionList = self.query_one("#datasets", SelectionList)
        selected_indices: list[int] = datasets_widget.selected

        if not selected_indices:
            self.notify("No datasets selected to add.", severity="warning")
            return

        datasets_to_load: List[Tuple[str, PurePath]] = []
        for index in selected_indices:
            # Ensure index is valid
            if index < len(datasets_widget.options):
                # Safely access the prompt text
                prompt_text_list = getattr(datasets_widget.options[index].prompt, '_text', None)
                if prompt_text_list and isinstance(prompt_text_list, list):# and prompt_text_list:
                    ds_name_base = prompt_text_list[0]
                    ds_name = ds_name_base + ".json"
                    # Determine source path based on whether the base name has numbers
                    has_numbers = any(char.isdigit() for char in ds_name_base)
                    source_p = self.root_data_dir if has_numbers else self.srch_data_dir
                    json_path = PurePath(Path.cwd(), source_p, Path(ds_name))
                    datasets_to_load.append((ds_name, json_path))
                else:
                     self.notify(f"Could not retrieve name for selection index {index}.", severity="warning")

            else:
                 self.notify(f"Selection index {index} is out of bounds.", severity="warning")


        if datasets_to_load:
            self.app.notify(f"Starting background load for {len(datasets_to_load)} dataset(s)...")
            # Pass the list of datasets to the worker
            self._add_multiple_datasets_worker(datasets_to_load)
        else:
             self.notify("No valid datasets found to load.", severity="warning")
        datasets_widget.deselect_all()


    @work(thread=True, exclusive=True, group="dataset_loading")
    async def _add_multiple_datasets_worker(self, datasets_info: List[Tuple[str, PurePath]]):
        """
        Worker thread to load multiple JSON files and update the tree safely.

        Args:
            datasets_info: A list of tuples, where each tuple contains
                           (dataset_name, dataset_path).
        """
        tree_view: TreeView = self.query_one("#tree-container", TreeView)
        # Ensure we get the actual JSONTree instance
        tree: JSONTree = tree_view.query_one(JSONTree) # Changed Tree to JSONTree
        worker = get_current_worker()
        total_datasets = len(datasets_info)

        for i, (ds_name, json_path) in enumerate(datasets_info):
            if worker.is_cancelled:
                self.app.call_from_thread(self.notify, "Dataset loading cancelled.")
                break

            self.app.call_from_thread(self.notify, f"Loading ({i+1}/{total_datasets}): {ds_name}")

            try:
                # Perform file I/O and JSON parsing in the worker thread
                with open(json_path, mode="r", encoding="utf-8") as f:
                    json_data_str = f.read()
                json_data = json.loads(json_data_str)
                cleaned_data = clean_string_values(json_data)

                # Update UI from the main thread ---
                # Define a helper function to perform the UI updates
                def update_tree_ui(name: str, data: Dict[str, Any]):
                    try:
                        # Check if node already exists to prevent duplicates
                        existing_labels = {node.label.plain for node in tree.root.children}
                        if name not in existing_labels:
                            new_node = tree.root.add(name) # Add the top-level node
                            tree.add_node(name, new_node, data) # Populate the node recursively
                            self.app.notify(f"Successfully added {name} to the tree.")
                        else:
                             self.app.notify(f"Dataset '{name}' already exists in the tree. Skipping.", severity="warning")
                    except Exception as ui_e:
                         # Log UI update errors specifically
                         logger.error(f"Error updating tree UI for {name}: {ui_e}")
                         self.app.notify(f"Error adding {name} to UI: {ui_e}", severity="error")

                # Schedule the UI update function to run on the main thread
                self.app.call_from_thread(update_tree_ui, name=ds_name, data=cleaned_data)
                # Take a power nap to allow UI thread processing time
                await asyncio.sleep(0.05)

            except FileNotFoundError:
                 logger.error(f"File not found for dataset: {ds_name} at {json_path}")
                 self.app.call_from_thread(self.notify, f"Error: File not found for {ds_name}", severity="error")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for {ds_name}: {e}")
                self.app.call_from_thread(self.notify, f"Error parsing JSON for {ds_name}: {e}", severity="error")
            except Exception as e:
                # Catch other potential errors during file reading or processing
                logger.error(f"Error loading dataset {ds_name}: {e}")
                self.app.call_from_thread(self.notify, f"Error loading {ds_name}: {e}", severity="error", timeout=5)

        self.app.call_from_thread(self.notify, f"Finished loading {total_datasets} dataset(s).")


    #FUNCTION - Remove Data
    def remove_datasets(self) -> None:
        tree_view: TreeView = self.query_one("#tree-container", TreeView)
        tree: Tree = tree_view.query_one(Tree)
        datasets: SelectionList = self.query_one("#datasets", SelectionList)
        selected: list = datasets.selected

        if len(selected) > 1:
            for itemid in selected:
                rem_conf = datasets.options[itemid].prompt._text[0] + ".json"
                for node in tree.root.children:
                    if rem_conf in node.label.plain:
                        self.app.notify(f"Removing {rem_conf}")
                        node.remove()
                        sleep(0.1)
        else:
            rem_conf = datasets.options[selected[0]].prompt._text[0] + ".json"
            for node in tree.root.children:
                if rem_conf in node.label.plain:
                    self.app.notify(f"Removing {rem_conf}")
                    node.remove()
                    sleep(0.1)
        datasets.deselect_all()

    #FUNCTION - run search
    def run_search(self) -> None:
        #FUNCTION - Is numeric string
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
                return False
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
                sims, paper_names = launch_cos(srch_text, field, node) 
                arr = np.array(sims, dtype=np.float32)
                qual_indexes = np.where(arr >= threshold)[0]
                if qual_indexes.shape[0] > 0:
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
                self.app.notify(f"{metric} search currently not available")
            elif metric == "Hamming":
                self.app.notify(f"{metric} search currently not available")
            elif metric == "Jaccard":
                self.app.notify(f"{metric} search currently not available")
            elif metric == "LCS":
                self.app.notify(f"{metric} search currently not available")
            
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
        
        #Progress bar loading
        searchbar = SearchProgress(total=len(tree.root.children), count=0)
        search_container = Container(searchbar, id="loading-container")
        tree_view: TreeView = self.query_one("#tree-container", TreeView)
        tree: Tree = tree_view.query_one(Tree)
        root_name = f"{SEARCH_METRICS[metric].lower()}_{SEARCH_FIELDS[field]}_{'-'.join(srch_text.lower().split())}"
        results = {}
        self.push_screen(search_container)
        searchbar.render()

        for node in tree.root.children:
            conf = node.label.plain.split()[1]
            self.app.notify(f"Searching {conf}")
            result = conf_search(srch_text, node, variables, conf)
            if result:
                results.update(**result)
            else:
                self.notify(f"No results found in {conf}")
            searchbar.advance(1)
            sleep(0.1)

        if results:
            self.load_data(tree, root_name, results)
            save_data(root_name, results)
            self.app.notify(f"{len(results.keys())} papers found in {len(tree.root.children)} conferences")

        else:
            self.app.notify("No results found in all datasets")
            sleep(2)
        
        if search_container.is_mounted:
            self.pop_screen(search_container)
        
    ##########################  Tree Functions ####################################
    #FUNCTION Tree Node select
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node in the tree is selected."""
        self.selected_node_data = event.node.data

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
        if not activetab.active == "content-tab":
            # tree_view = self.query_one(TreeView)
            # tree = tree_view.query_one(JSONTree)
            tree = self.query_one(TreeView)
            json_docview.focus()
            tree.focus()

    #FUNCTION Screenshot
    def action_screenshot(self):
        current_time = get_c_time()
        self.save_screenshot(f"{current_time}.svg", "./data/screenshots/" )
    
    #FUNCTION toggle root
    def action_toggle_root(self) -> None:
        # tree = self.query_one(JSONTree)
        tree = self.query_one(TreeView)
        tree.show_root = not tree.show_root
