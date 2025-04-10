from __future__ import annotations
#Main imports
import json
import sys
import numpy as np
from typing import TYPE_CHECKING, Optional
from pathlib import Path, PurePath
#Textual Imports
from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.reactive import reactive, var
from textual import work
from asyncio import sleep
from widgets import JSONDocumentView, JSONTree, TreeView
from textual.containers import Container, Horizontal
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
from utils import clean_string_values, get_c_time
from support import list_datasets, SEARCH_KEYS, SEARCH_METRICS

if TYPE_CHECKING:
    from io import TextIOWrapper

__prog_name__ = "jtree_ML"
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
    srch_data_dir = var(Path("./data/search_results/"))
    selected_node_data:  reactive[object | None] = reactive(None)
    all_datasets: list[Path] = list_datasets([root_data_dir, srch_data_dir])

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
                        yield Input("Type search here", id="search-input")
                        yield Static("Search Field", id="field-hdr", classes="header")
                        yield Static("Search Metrics", id="metric-hdr", classes="header")
                        yield Input("Result Limit", id="input-limit", type="integer")
                        with RadioSet(id="radio-fields", classes="header"):
                            for field in SEARCH_KEYS:
                                yield RadioButton(field)
                        with RadioSet(id="radio-metrics", classes="header"):
                            for field in SEARCH_METRICS:
                                yield RadioButton(field)
                        yield Button("Search Datasets", id="search-button")
                        

                    # yield Static("Search functionality will be implemented here.", id="search-placeholder")
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

    def on_mount(self) -> None:
        tree_view = self.query_one(TreeView)
        tree = tree_view.query_one(JSONTree)
        # tree.loading = True
        root_name = self.json_name
        json_data = self.load_data(tree, root_name, self.json_data)
        json_docview = self.query_one(JSONDocumentView)
        json_docview.update_document(json_data)
        # tree.loading = False
        tree.focus()

    def load_data(self, json_tree: TreeView, root_name:str, json_data:dict) -> dict | None:
        json_node = json_tree.root.add(root_name)
        json_data = clean_string_values(json.loads(json_data))
        json_tree.add_node(root_name, json_node, json_data)
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
        
        if button_id == "add-button":
            button = self.query_one("#add-button", Button)
            button.loading = True
            for itemid in selected:
                new_json = datasets.options[itemid].prompt._text[0] + ".json"
                json_path = PurePath(Path.cwd(), self.root_data_dir, Path(new_json))
                json_data = open(json_path, mode="r", encoding="utf-8").read()
                self.load_data(tree, new_json, json_data)
            button.loading = False

        elif button_id == "rem-button":
            for itemid in selected:
                rem_conf = datasets.options[itemid].prompt._text[0] + ".json"
                for node in tree.root.children:
                    if rem_conf in node._label:
                        node.remove()

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
#TODO - Add LoadingIndicator for button widgets
    #look at venvkiller for how he did that. probalby a custom class

#Search workflow. 
#- When you select a search field. 
    #Other fields in the search metrics will enable/disable
#- That way you won't have unmapped search paths

#Possible Search paths
#1. Basic text match searching.  
    #This can be run with the following

