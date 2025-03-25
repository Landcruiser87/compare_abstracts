from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import Container
from textual.widgets import Footer, Header, Tree
from support import logger
from utils import clean_string_values, get_c_time
from widgets import JSONDocumentView, JSONTree, TreeView

if TYPE_CHECKING:
    from io import TextIOWrapper

__prog_name__ = "jtree_ML"
__version__ = "0.2.8"   

class JSONTreeApp(App):
    TITLE = __prog_name__
    SUB_TITLE = f"A JSON Tree Viewer for Machine Learning Papers ({__version__})"
    CSS_PATH = "css/layout.tcss"
    show_abstract = False
    BINDINGS = [
        ("ctrl+s", "app.screenshot()", "Screenshot"),
        ("ctrl+t", "toggle_root", "Toggle root"),
        ("enter", "display_selected", "Display Selected"),  
        Binding("q", "app.quit", "Quit"),
    ]

    json_data: reactive[str] = reactive("")
    json_name: str = ""
    selected_node_data:  reactive[object | None] = reactive(None)

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
        self.json_name = json_file.name.split("/")[-1]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            TreeView(id="tree-view"), JSONDocumentView(id="json-docview"), id="app-grid"
        ) 
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
        tree.focus()

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
