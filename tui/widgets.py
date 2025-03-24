from __future__ import annotations
import json
from rich.highlighter import ReprHighlighter
from rich.syntax import Syntax
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static, Tree
from textual.widgets.tree import TreeNode

highlighter = ReprHighlighter()

class JSONDocument(Static):
    def load(self, json_data: str) -> bool:
        try:
            json_doc = Syntax(json_data, lexer="json", word_wrap=True)
        except Exception as e:
            return False
        self.update(json_doc)
        return True

class JSONDocumentView(Vertical):
    DEFAULT_CSS = """
    JSONDocumentView {
        height: 1fr;
        overflow: auto;
    }

    JSONDocumentView > Static {
        width: auto;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield JSONDocument(id="json-document")

    def update_document(self, json_data: dict) -> None:
        self.current_json_data = json_data
        json_doc = self.query_one("#json-document", JSONDocument)
        if isinstance(json_data, dict):
            if "abstract" in list(json_data.values()):
                json_doc.load(json.dumps(json_data.get("abstract")))
            else:
                json_doc.load(json.dumps(json_data, indent=4))
        self.refresh()

class JSONTree(Tree):
    def add_node(self, name: str, node: TreeNode, data: object) -> None:
        """Adds a node to the tree.

        Args:
            name (str): Name of the node.
            node (TreeNode): Parent node.
            data (object): Data associated with the node.
        """
        if isinstance(data, dict):
            node._label = Text(f"{{}} {name}")
            for key, value in data.items():
                new_node = node.add("")
                self.add_node(key, new_node, value)
                new_node.data = value
        elif isinstance(data, list):
            node._label = Text(f"{name}")
            for index, value in enumerate(data):
                new_node = node.add("")
                self.add_node(str(index), new_node, value)
                new_node.data = value
        else:
            node._allow_expand = False
            if name:
                label = Text.assemble(
                    Text.from_markup(f"[b]{name}[/b]="), highlighter(repr(data))
                )
            else:
                label = Text(repr(data))
            node._label = label
            node.data = data

class TreeView(Widget, can_focus_children=True):
    def compose(self) -> ComposeResult:
        tree = JSONTree("Root")
        tree.show_root = False
        yield tree