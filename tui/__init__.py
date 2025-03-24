from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Tree

from utils import clean_string_values, get_c_time
from widgets import JSONDocument, JSONDocumentView, JSONTree, TreeView

if TYPE_CHECKING:
    from io import TextIOWrapper

__prog_name__ = "jtree_andy"
__version__ = "0.2.8"


class JSONTreeApp(App):
    TITLE = __prog_name__
    SUB_TITLE = f"A JSON Tree Viewer ({__version__})"
    CSS_PATH = "css/layout.tcss"

    BINDINGS = [
        ("ctrl+s", "app.screenshot()", "Screenshot"),
        ("ctrl+t", "toggle_root", "Toggle root"),
        Binding("tab", "focus_next", "Focus Next"),
        Binding("q", "app.quit", "Quit"),
    ]

    def __init__(
        self,
        json_file: TextIOWrapper,
        driver_class=None,
        css_path=None,
        watch_css=False,
    ):
        super().__init__(driver_class, css_path, watch_css)
        self.json_data: str = ""
        self.json_name: str = json_file.name.split("/")[-1]

        if json_file is sys.stdin:
            self.json_data = "".join(sys.stdin.readlines())
        else:
            self.json_data = json_file.read()
            json_file.close()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            TreeView(id="tree-view"), JSONDocumentView(id="json-docview"), id="app-grid"
        ) 
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "textual-dark"
        tree_view = self.query_one(TreeView)
        tree = tree_view.query_one(JSONTree)
        root_name = self.json_name
        json_node = tree.root.add(root_name)
        json_data = clean_string_values(json.loads(self.json_data))
        tree.add_node(root_name, json_node, json_data)
        json_docview = self.query_one(JSONDocumentView)
        json_docview.update_document(json_data)
        tree_view.focus()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node in the tree is selected."""
        event.stop()
        node_data = event.node.data
        json_docview = self.query_one(JSONDocumentView)
        if node_data is not None:
            json_docview.update_document(node_data)
        elif event.node.allow_expand:
            # If it's a parent node, display its structure (first level of children)
            data = {}
            for child in event.node.children:
                data[child._label.plain.split("=")[0].strip().lstrip("{}")] = child.data
            json_docview.update_document(data)
        else:
            # Handle leaf nodes without explicit data (shouldn't happen with this tree structure)
            json_docview.query_one("#json-document", JSONDocument).update("")

    def action_screenshot(self):
        current_time = get_c_time()
        self.save_screenshot(f"./data/screenshots/{current_time}.svg")

    def action_toggle_root(self) -> None:
        tree_view = self.query_one(TreeView)
        tree = self.query_one(JSONTree)
        tree.show_root = not tree.show_root
    
    def action_focus_next(self) -> None:
        if self.focused is self.query_one(TreeView):
            self.query_one(JSONDocumentView).focus()
        else:
            self.query_one(TreeView).focus()