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

# class JSONDocument(Static):
#     def load(self, json_data: str) -> bool:
#         try:
#             if isinstance(json_data, str):
#                 json_doc = Syntax(json_data, lexer="python", theme="github-dark", word_wrap=True)
#             elif isinstance(json_data, (dict, list)):
#                 json_doc = Syntax(json_data, lexer="json", theme="github-dark", word_wrap=True)
#             self.update(json_doc)
#             return True
#         except Exception as e:
#             # Display the error in the JSONDocument.  Good for debugging.
#             self.update(f"Error parsing JSON: {e}")
#             return False

class JSONDocument(Static):
    def load(self, json_data: str) -> bool:
        try:
            if isinstance(json_data, str):
                json_doc = Syntax(json_data, lexer="python", theme="github-dark", word_wrap=True)
            elif isinstance(json_data, (dict, list)):
                json_doc = Syntax(json_data, lexer="json", theme="github-dark", word_wrap=True)
            self.update(json_doc)
            return True
        except Exception as e:
            # Display the error in the JSONDocument.  Good for debugging.
            self.update(f"Error parsing JSON: {e}")
            return False


class JSONDocumentView(Vertical):
    DEFAULT_CSS = """
    JSONDocumentView {
        height: 1fr;
        overflow-y: auto;
        overflow-x: hidden;
    }

    JSONDocumentView > Static {
        width: auto;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield JSONDocument(id="json-document")

    def update_document(self, json_data: str) -> None:
        json_doc = self.query_one("#json-document", JSONDocument)
        json_doc.load(json_data)
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