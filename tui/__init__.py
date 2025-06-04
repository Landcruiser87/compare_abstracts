from __future__ import annotations
#Main imports
import json
import sys
import asyncio
import numpy as np
import re
from time import sleep
from typing import TYPE_CHECKING, List, Tuple, Dict, Any 
from pathlib import Path, PurePath
from collections import deque
from torch.cuda import empty_cache
#Textual Imports
from textual import on, work
from textual.binding import Binding
from textual.app import App, ComposeResult
from widgets import (
    JSONDocumentView,JSONTree,
    TreeView,SearchProgress
)
from textual.containers import Container, Horizontal, Vertical
from textual.fuzzy import Matcher
from textual.worker import get_current_worker
from textual.reactive import reactive, var
from textual.widgets import (
    Button,Footer,Header,
    Input,Static,SelectionList,
    RadioButton,RadioSet, 
    TabbedContent,TabPane,Tree
)
from textual.widgets.selection_list import Selection
from textual.widgets.tree import TreeNode
from sentence_transformers import util as st_utils
#Custom Imports
from utils import (
    ArxivSearch,sbert,word2vec,
    tfidf,get_c_time,clean_text,
    cosine_similarity,clean_string_values
)

from support import (
    list_datasets, save_data, logger, #functions
    SEARCH_FIELDS, SEARCH_MODELS, MODEL_DESC, #global vars
    ARXIV_FIELDS, ARXIV_SUBJECTS, ARXIV_DATES, ARXIV_AREAS #arXiv vars
)
if TYPE_CHECKING:
    from io import TextIOWrapper

__prog_name__ = "ML_Tree"
__version__ = "0.3.2"

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

                # Tab 2 - Manage Datasets - Buttons and SelectionList
                with TabPane("Manage Datasets", id="manage-tab"):
                    with Horizontal(id="dataset-container"):
                        with Container(id="dc-leftside"):
                            yield Static("Available Datasets", id="data-title", classes="header")
                            yield SelectionList(*self.all_datasets, name="Dataset List", id="datasets")

                        with Container(id="dc-rightside"):
                            yield Button("Add Dataset", id="add-button")
                            yield Button("Remove Dataset", id="rem-button")

                # Tab 3 - Datasets Search
                with TabPane("Search Datasets", id="search-tab"):
                    with Container(id="srch-container"):
                        yield Input("Type search here", id="input-search")
                        yield Static("Search Models", id="hdr-model", classes="header")
                        yield Static("Search Field", id="hdr-field", classes="header")
                        yield Static("Search Params", id="hdr-param", classes="header")
                        
                        with RadioSet(id="radio-models", classes="header"):
                            for model, tip in zip(SEARCH_MODELS, MODEL_DESC):
                                yield RadioButton(model, tooltip=tip)
                        with RadioSet(id="radio-fields", classes="header"):
                            for field in SEARCH_FIELDS:
                                yield RadioButton(field)
                        with Container(id="sub-container"):
                            with Vertical(id="srch-fields"):
                                yield Input("res limit", tooltip="Limit the amount of returned results", id="input-limit", type="integer")
                                yield Input("threshold", tooltip="Threshold the appropriate metric", id="input-thres", type="number")
                            yield Button("Search Datasets", tooltip="Run like ya stole something!", id="search-button")

                # Tab 4 - arXiv Search
                with TabPane("Search arXiv", id="arxiv-tab"):
                    with Container(id="srch-arx-container"):
                        yield Input("Type search here", id="input-arxiv", tooltip="for explicit query formatting details visit\nhttps://info.arxiv.org/help/api/user-manual.html#query_details")
                        yield Static("Search Field\nDate Range", id="hdr-arx-cat", classes="header")
                        yield Static("Subject", id="hdr-arx-sub", classes="header")
                        yield Static("Category", id="hdr-arx-date", classes="header")
                        yield Static("Limits", id="hdr-arx-limit", classes="header")
                        with Vertical(id="arx-radios"):
                            with RadioSet(id="radio-arx-cat", classes="header"):
                                for cat in ARXIV_FIELDS:
                                    yield RadioButton(cat)
                            with RadioSet(id="radio-arx-dates", classes="header"):
                                for dfield in ARXIV_DATES:
                                    yield RadioButton(dfield)
                        with RadioSet(id="radio-arx-subjects", classes="header", tooltip="Leave categories (next section) blank to search all"):
                            for subject in ARXIV_SUBJECTS:
                                yield RadioButton(subject)
                        yield SelectionList(name="Category", id="sl-arx-categories")
                        with Vertical(id="sub-arx-limit"):
                            yield Input("Result limit", tooltip="Limit the amount of returned results.  200 is the max you can request", id="input-arx-limit", type="integer")
                            yield Input("Date From", tooltip="Specific Year Ex:2025\nDate Range Ex: YYYY-MM-DD", id="input-arx-from", type="text")
                            yield Input("Date To", tooltip="Ex: 2025-4-12", id="input-arx-to", type="text", disabled=True)
                            yield Button("Search arXiv", tooltip="For search tips go to\nhttps://arxiv.org/search/advanced", id="search-arxiv")
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

    @on(SelectionList.SelectedChanged, "#datasets")
    def on_datasets_selection_changed(self, event: SelectionList.SelectedChanged) -> None:
        abutton = self.query_one("#add-button", Button)
        rbutton = self.query_one("#rem-button", Button)
        selections = len(event.selection_list.selected)
        if selections > 0:
            abutton.label = f"Add {selections} datasets"
            rbutton.label = f"Remove {selections} datasets"
        else:
            abutton.label = f"Add Data"
            rbutton.label = f"Remove Data"

    @on(RadioSet.Changed, "#radio-models")
    def on_radio_models_changed(self, event: RadioSet.Changed) -> None:
        input_thres = self.query_one("#input-thres", Input)
        if "Fuzzy" in event.pressed.label:
            met_range = "-1 to 1"
            suggested = 0.25
            input_thres.tooltip = f"Input threshold\nFuzzy:{met_range}\nSuggested:{suggested}"
        elif "Cosine" in event.pressed.label:
            met_range = "-1 to 1"
            suggested = 0.5
            input_thres.tooltip = f"Input threshold\nCosine: {met_range}\nSuggested:{suggested}"
        elif "Word2Vec" in event.pressed.label:
            met_range = "-1 to 1"
            suggested = 0.85
            input_thres.tooltip = f"Input threshold\nWord2Vec: {met_range}\nSuggested:{suggested}"
        elif "Marco" in event.pressed.label:
            met_range = "-1 to 1"
            suggested = 0.25
            input_thres.tooltip = f"Input threshold\nMarco: {met_range}\nSuggested:{suggested}"
        elif "Specter" in event.pressed.label:
            met_range = "-1 to 1"
            suggested = 0.5
            input_thres.tooltip = f"Input threshold\nSpecter: {met_range}\nSuggested:{suggested}"


    @on(RadioSet.Changed, "#radio-arx-dates")
    def on_radioset_arx_dates_changed(self, event: RadioSet.Changed) -> None:
        dateto = self.query_one("#input-arx-to", Input)
        if "Date Range" in event.pressed.label:
            dateto.disabled = False
        else:
            dateto.disabled = True


    @on(RadioSet.Changed, "#radio-arx-subjects")
    def on_radio_subjects_changed(self, event: RadioSet.Changed) -> None:
        categories = self.query_one("#sl-arx-categories", SelectionList)
        categories.clear_options()
        pressed = getattr(event.pressed.label, '_text', None)[0]
        for key, val in ARXIV_AREAS.items():
            if key == pressed:
                codes = [Selection(y, x, False) for x, y in enumerate(val.keys())]
                categories.add_options(codes)
                break

    #Old code for SelectionList behavior.  Saving for now as I might go back to it. 
    # @on(SelectionList.SelectionHighlighted, "#arx-subjects")
    # def on_arx_subjects_highlighted(self, event: SelectionList.SelectionHighlighted) -> None:
    #     categories = self.query_one("#sl-arx-categories", SelectionList)
    #     categories.clear_options()
    #     selections = event.selection_list.selected
    #     if len(selections) > 0:
    #         for selection in selections:
    #             for key, val in ARXIV_AREAS.items():
    #                 if ARXIV_SUBJECTS[selection][0] in key:
    #                     codes = [Selection(y, x, False) for x, y in enumerate(val.keys())]
    #                     categories.add_options(codes)

    @on(SelectionList.SelectionHighlighted, "#sl-arx-categories")
    def on_arx_categories_highlighted(self, event: SelectionList.SelectionHighlighted) -> None:
        categories = self.query_one("#sl-arx-categories", SelectionList)
        if event.selection_list.selected:
            selected = getattr(categories.options[event.selection_list.selected[-1]].prompt, '_text', None)
            tips = [[(k2, v2) for k2, v2 in v2.items() if k2==selected[0]] for _, v2 in ARXIV_AREAS.items()]
            tips = list(filter(None, tips))
            categories.tooltip = tips[0][0][0]+ "\n" + "\n".join(tips[0][0][1])
        else:
            categories.tooltip = None

    @on(Button.Pressed, "#add-button")
    def add_button_event(self):
        self.add_datasets()

    @on(Button.Pressed, "#rem-button")
    def remove_button_event(self):
        self.remove_datasets()

    @on(Button.Pressed, "#search-button")
    def search_button_event(self):
        self.run_search()

    @on(Button.Pressed, "#search-arxiv")
    def arxiv_button_event(self):
        self.search_arxiv()

    #FUNCTION - Load Data
    def load_data(self, json_tree: TreeView, root_name:str, json_data:dict|str) -> dict:
        new_node = json_tree.root.add(root_name)
        if isinstance(json_data, str):
            json_data = clean_string_values(json.loads(json_data))
            json_tree.add_node(root_name, new_node, json_data)
            return json_data
        elif isinstance(json_data, dict):
            json_data = clean_string_values(json_data)
            json_tree.add_node(root_name, new_node, json_data)


    #FUNCTION - Remove Data
    def remove_datasets(self) -> None:
        tree_view: TreeView = self.query_one("#tree-container", TreeView)
        tree: Tree = tree_view.query_one(Tree)
        datasets: SelectionList = self.query_one("#datasets", SelectionList)
        selected: list = datasets.selected

        if len(selected) > 1:
            for itemid in selected:
                rem_conf = getattr(datasets.options[itemid].prompt, '_text', None)[0]
                # rem_conf = datasets.options[itemid].prompt._text[0] + ".json"
                for node in tree.root.children:
                    if rem_conf in node.label.plain:
                        self.app.notify(f"Removing {rem_conf}")
                        node.remove()
                        sleep(0.1)
        else:
            rem_conf = getattr(datasets.options[selected[0]].prompt, '_text', None)[0]
            # rem_conf = datasets.options[selected[0]].prompt._text[0] + ".json"
            for node in tree.root.children:
                if rem_conf in node.label.plain:
                    self.app.notify(f"Removing {rem_conf}")
                    node.remove()
                    sleep(0.1)
        datasets.deselect_all()

    def reload_datasets(self) -> None:
        #Manually refresh SelectionList options to avoid index errors
        datasets = self.query_one("#datasets", SelectionList)
        datasets.clear_options()
        self.all_datasets = list_datasets()
        new_datasets = [
            Selection(s[0], s[1], False)
            for s in self.all_datasets
        ]
        datasets.add_options(new_datasets)

    def is_numeric_string(self, s: str) -> bool:
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
    def launch_cos(self, srch_txt:str, srch_field:str, node:Tree):
        fields, paper_names = clean_text(srch_txt, srch_field, node)
        tfid, paper_names = tfidf(fields, paper_names)
        sims = cosine_similarity(tfid, "scipy")
        return sims[1:], paper_names[1:]

    #FUNCTION - launch word2vec
    def launch_word2vec(self, srch_txt:str, srch_field:str, node:Tree):
        nlp = word2vec()
        fields, paper_names = clean_text(srch_txt, srch_field, node)
        target = nlp(srch_txt)
        sims = []
        for field in fields:
            corpus = nlp(field)
            sim = target.similarity(corpus)
            sims.append(sim)

        return sims[1:], paper_names[1:]

    #FUNCTION - launch sbert
    def launch_sbert(self, srch_txt:str, srch_field:str, node:Tree, metric:str):
        bert, device = sbert(metric)
        fields, paper_names = clean_text(srch_txt, srch_field, node)
        query_embedding = bert.encode(srch_txt, convert_to_tensor=True)
        corpus_embedding = bert.encode(fields, convert_to_tensor=True, batch_size=100)
        if metric == "Marco":
            search_res = st_utils.cos_sim(query_embedding, corpus_embedding)
            if device == "cpu":
                sims = search_res.numpy().flatten()
            else:
                sims = search_res.cpu().numpy().flatten()
            logger.info(f"{metric} {sims.shape}")
            
        elif metric == "Specter":
            search_res = st_utils.semantic_search(query_embedding, corpus_embedding)
            search_res = search_res[0]
            sims = np.array([res["score"] for res in search_res])
            papers = [paper_names[res["corpus_id"]] for res in search_res]
            paper_names = papers
            logger.info(f"{metric} {sims.shape}")

            #BUG - Specter Model
                #The specter model on abstract (what its designed for) is quite slow
                #Not sure how to speed that up.
        
        #Delete the model and empty the cache
        del bert
        if device == "cuda":
            empty_cache()

        return sims[1:], paper_names[1:]

    #FUNCTION conf search
    def conf_search(
            self,
            srch_text:str, 
            node:Tree, 
            variables:list,
            conf:str
        ):
        #Load variables
        results = {}
        metric = SEARCH_MODELS[variables[0]]
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

        elif metric in ["Cosine", "Word2Vec", "Marco", "Specter"]:
            if metric == "Cosine":
                sims, paper_names = self.launch_cos(srch_text, field, node) 
            elif metric == "Word2Vec":
                sims, paper_names = self.launch_word2vec(srch_text, field, node)
            elif (metric == "Marco") | (metric == "Specter"):
                sims, paper_names = self.launch_sbert(srch_text, field, node, metric)
            else:
                self.app.notify("Something broke", severity="error")
                raise ValueError("Something broke, check me! Line 412")
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
        else:
            self.app.notify(f"{metric} search currently not available")
            return
        
        res = sorted(results.items(), key=lambda x:x[1].get("metric_match"), reverse=True)[:res_limit]
        return dict(res)
    
    def add_datasets(self):
        """Handles the 'Add Dataset' button press by launching a worker."""
        datasets: SelectionList = self.query_one("#datasets", SelectionList)
        selected_indices: list[int] = datasets.selected

        if not selected_indices:
            self.notify("No datasets selected to add.", severity="warning")
            return

        datasets_to_load: List[Tuple[str, PurePath]] = []
        for index in selected_indices:
            # Ensure index is valid
            if index <= len(datasets.options):
                # Safely access the prompt text
                prompt_text_list = getattr(datasets.options[index].prompt, '_text', None)
                if prompt_text_list and isinstance(prompt_text_list, list):# and prompt_text_list:
                    ds_name_base = prompt_text_list[0]
                    ds_name = ds_name_base + ".json"
                    # Determine source path based on whether the base name has numbers
                    has_a_year = re.search(r"\d{4}", ds_name)
                    source_p = self.root_data_dir if has_a_year else self.srch_data_dir
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
        datasets.deselect_all()

    @work(thread=True, exclusive=True, group="dataset_loading")
    async def _add_multiple_datasets_worker(self, datasets_info: List[Tuple[str, PurePath]]):
        """
        Worker thread to load multiple JSON files and update the tree safely.

        Args:
            datasets_info: A list of tuples, where each tuple contains
                           (dataset_name, dataset_path).
        """
        tree_view: TreeView = self.query_one("#tree-container", TreeView)
        tree: JSONTree = tree_view.query_one(JSONTree) 
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
                            self.app.notify(f"Successfully added {name}")
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
                self.app.call_from_thread(self.notify, f"Error loading {ds_name}: {e}", severity="error", timeout=2)

        self.app.call_from_thread(self.notify, f"Finished loading {total_datasets} dataset(s).")


    #FUNCTION - run search
    def run_search(self) -> None:
        #query needed widgets
        srch_text = self.query_one("#input-search", Input).value
        model = self.query_one("#radio-models", RadioSet)._reactive__selected
        field = self.query_one("#radio-fields", RadioSet)._reactive__selected
        res_limit = self.query_one("#input-limit", Input).value
        threshold = self.query_one("#input-thres", Input).value
        #bind the info together in a tuple
        variables = [model, field, res_limit, threshold]
        if not all(self.is_numeric_string(str(var)) for var in variables):
            self.notify("Search inputs are malformed.\nCheck inputs (int or float) and try again", severity="error")
            return

        tree_view: TreeView = self.query_one("#tree-container", TreeView)
        tree: Tree = tree_view.query_one(Tree)
        sources: list = list(tree.root.children)
        searchbar = SearchProgress(count=0, total=len(sources))
        self.search_container = Container(searchbar, id="loading-container")
        root_name = f"{SEARCH_MODELS[model].lower()}_{SEARCH_FIELDS[field]}_{'-'.join(srch_text.lower().split())}"
        self.mount(self.search_container)
        self._search_datasets_worker(srch_text, variables, sources, root_name, tree)

    @work(thread=True, exclusive=True, group="dataset_searching")
    async def _search_datasets_worker(
        self, 
        srch_text:str, 
        variables: list,
        sources: List[TreeNode],
        root_name: str,
        tree: Tree
        ):
        """Worker thread to search JSON files.

        Args:
            srch_text (str): _description_
            variables (list): _description_
            sources (List[TreeNode]): _description_
            root_name (str): _description_
            tree (Tree): _description_
        """
        worker = get_current_worker()
        total_datasets = len(sources)
        all_results = {}
        srchcount = 0
        try:
            for node in sources:
                if worker.is_cancelled:
                    self.app.call_from_thread(self.notify, "Search cancelled.")
                    break
                
                conf_name = node.label.plain.strip("{}").strip()
                self.app.call_from_thread(self.notify, f"Searching ({srchcount+1}/{total_datasets}): {conf_name}")
                
                # Perform JSON parsing in the worker thread
                result = self.conf_search(srch_text, node, variables, conf_name)
                if result:
                    all_results.update(**result)
                srchcount += 1
                # Define a helper function to perform the UI updates
                def update_progress_ui(current_count:int):
                    if self.search_container and self.search_container.is_mounted:
                        try:
                            progress_bar = self.search_container.query_one(SearchProgress)
                            progress_bar.count = current_count
                            progress_bar.advance(1)
                            progress_bar.refresh()

                        except Exception as e:
                             logger.error(f"Failed to update search progress bar: {e}")

                # Schedule the UI update function to run on the main thread
                self.app.call_from_thread(update_progress_ui, srchcount)
                # Take a power nap to allow UI thread processing time
                await asyncio.sleep(0.1)

            if not worker.is_cancelled:                
                if all_results:
                    self.app.call_from_thread(self.load_data, tree, root_name, all_results)
                    try:
                        save_data(root_name, all_results)
                        self.app.call_from_thread(self.notify, f"Found {len(all_results.keys())} papers in {total_datasets} sources.")

                    except Exception as e:
                        logger.error(f"Failed to save saerch results: {e}")

                else:
                    self.app.call_from_thread(self.notify, "Search Complete, No results found")
                    sleep(2)

        except Exception as e:
            # Catch other potential errors during json traversal
            logger.error(f"Error during worker run: {e}")
            self.app.call_from_thread(self.notify, f"Search Failed {conf_name}: {e}", severity="error", timeout=2)

        finally:
            # Remove Progress Bar
            def remove_progress_ui():
                if self.search_container and self.search_container.is_mounted:
                    try:
                        self.search_container.remove()
                        logger.info("Search progress container removed.")
                        
                    except Exception as e:
                        logger.error(f"Error removing search progress container: {e}")
                self.search_container = None 
            self.app.call_from_thread(remove_progress_ui)
            #Reload SelectionList to include search results
            self.reload_datasets()

    def search_arxiv(self):
        #Load up search variables
        variables = []
        srch_text = self.query_one("#input-arxiv", Input)._reactive_value
        start_date = self.query_one("#input-arx-from", Input)._reactive_value
        end_date_input = end_date = self.query_one("#input-arx-to", Input)
        end_date = end_date_input._reactive_value
        limit = self.query_one("#input-arx-limit", Input)._reactive_value
        field = self.query_one("#radio-arx-cat", RadioSet)._reactive__selected
        date_range = self.query_one("#radio-arx-dates", RadioSet)._reactive__selected
        subject = self.query_one("#radio-arx-subjects", RadioSet)._reactive__selected
        categories = self.query_one("#sl-arx-categories", SelectionList)
        selected_cat = self.query_one("#sl-arx-categories", SelectionList).selected
        root_name = f"arxiv_{ARXIV_FIELDS[field].lower()}_{"_".join(ARXIV_SUBJECTS[subject].lower().split(" "))}_{'-'.join(srch_text.lower().split())}"

        #bind the info together into a list
        variables = [limit, field, date_range, subject]
        if not all(self.is_numeric_string(str(var)) for var in variables):
            self.notify("Search inputs are malformed.\nCheck inputs and try again", severity="error")
            return None

        #Remap the variables with their values     
        variables = {
            "query"     : srch_text,
            "limit"     : limit,
            "field"     : ARXIV_FIELDS[field].lower(),
            "subject"   : ARXIV_SUBJECTS[subject],
            "categories":[getattr(categories.options[cat].prompt, '_text', None)[0] for cat in selected_cat],
            "dates"     : ARXIV_DATES[date_range],
            "start_date": "",
            "end_date"  : "",
            "year"      : "",
            "add_cat"   : False
        }
        
        #TODO - Need to update the term searching to how they do it. 
        #add an AND/OR button or someway to separate individual terms. 

        if not end_date_input.disabled:
            variables["start_date"] = start_date
            variables["end_date"] = end_date
        else:
            if ARXIV_DATES[date_range] == "Specific Year":
                variables["year"] = start_date

        arxiv = ArxivSearch(variables)
        json_data, no_res_message = arxiv.request_papers()
        if json_data:
            #Select the Tree object
            tree_view: TreeView = self.query_one("#tree-container", TreeView)
            tree: Tree = tree_view.query_one(Tree)

            try:
                self.notify(f"{len(json_data)} papers found on arXiv searching {variables["query"]} in subject {variables["subject"]}")
                #load the JSON into the Tree
                self.load_data(tree, root_name, json_data)
                #save the search
                save_data(root_name, json_data)
                self.reload_datasets()

            except Exception as e:
                logger.error(f"Failed to save search results: {e}")
        elif no_res_message:
            self.notify(f"{no_res_message}", severity="warning")
        else:
            self.notify(f"No papers matched the search {variables['query']}", severity="warning")
            logger.warning(f"No papers found the search {variables['query']}")

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
        tree_view: TreeView = self.query_one("#tree-container", TreeView)
        tree: JSONTree = tree_view.query_one(JSONTree) 
        tree.show_root = not tree.show_root
# ref https://www.newscatcherapi.com/blog/ultimate-guide-to-text-similarity-with-python#toc-3
