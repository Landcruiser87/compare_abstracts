from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Optional

from support import list_datasets
from pathlib import Path
from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.reactive import reactive, var

from utils import clean_string_values, get_c_time
from widgets import JSONDocumentView, JSONTree, TreeView
from textual.containers import Container
from textual.widgets import (
    Button, 
    Footer,
    Header,
    Static,
    SelectionList, 
    TabbedContent, 
    TabPane,       
    Tree
)

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
    selected_node_data:  reactive[object | None] = reactive(None)
    all_dataset: list[Path] = list_datasets([root_data_dir, Path("./data/search_results/")])
    dataset_list: SelectionList[int] =  SelectionList(*all_dataset)
    
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
                    yield Static("Search functionality will be implemented here.", id="search-placeholder")
                # Tab 3 - Manage Datasets - Buttons and SelectionList
                with TabPane("Manage Datasets", id="manage-tab"):
                    with Container(id="dataset-container"):
                        yield Button("Add Dataset", id="add-button")
                        yield Button("Remove Dataset", id="rem-button")
                        yield Static("Available Datasets", id="data-title", classes="header")
                        yield Static("Select Stuff", id="datasets")
                        # yield SelectionList("Dataset List", id="dataset-list")

        yield Footer()

    def on_mount(self) -> None:
        tree_view = self.query_one(TreeView)
        tree = tree_view.query_one(JSONTree)
        root_name = self.json_name
        json_node = tree.root.add(root_name)
        json_data = clean_string_values(json.loads(self.json_data))
        tree.add_node(root_name, json_node, json_data)
        json_docview = self.query_one(JSONDocumentView)
        json_docview.update_document(json_data)
        tabbed_doc = self.query(TabbedContent)
        tabbed_doc.focus()
        # tree.focus()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node in the tree is selected."""
        self.selected_node_data = event.node.data

    def watch_selected_node_data(self, new_data: object | None) -> None:
        """Watches for changes to selected_node_data and updates the display."""
        json_docview = self.query_one(JSONDocumentView)

        if new_data is not None:
            if isinstance(new_data, (dict, list, str, int)):
                json_docview.update_document(new_data)
        else:
             json_docview.update_document("")

    def action_screenshot(self):
        current_time = get_c_time()
        self.save_screenshot(f"{current_time}.svg", "./data/screenshots/" )

    def action_toggle_root(self) -> None:
        tree = self.query_one(JSONTree)
        tree.show_root = not tree.show_root