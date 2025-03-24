from __future__ import annotations

import json
from rich.highlighter import ReprHighlighter
from rich.syntax import Syntax
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static, Tree, TextArea
from textual.widgets.tree import TreeNode

highlighter = ReprHighlighter()

class JSONDocument(TextArea):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.read_only = True  # Ensure it's not editable

    def load(self, json_data: str) -> bool:
        try:
            # TODO: Customize theme="github-dark"
            json_doc = Syntax(json_data, lexer="json", line_numbers=True)
            self.text = str(json_doc)
            return True
        except Exception as e:
            return False

    def load_text(self, text: str) -> bool:
        self.text = text
        return True


class JSONDocumentView(Vertical):
    DEFAULT_CSS = """
    JSONDocumentView {
        height: 1fr;
        overflow: auto;
    }

    JSONDocumentView > TextArea {
        width: auto;
        height: auto;
        padding: 1;
        scrollbar-gutter: stable; /* Prevent layout shifts from scrollbar */
    }
    """

    BINDINGS = [
        ("a", "scroll_abstract", "Scroll Abstract"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_json_data: dict | None = None

    def compose(self) -> ComposeResult:
        yield JSONDocument(id="json-document")

    def update_document(self, json_data: dict) -> None:
        self.current_json_data = json_data
        json_doc = self.query_one("#json-document", JSONDocument)
        json_doc.load(json.dumps(json_data, indent=4))
        self.refresh()

    def action_scroll_abstract(self) -> None:
        if self.current_json_data and "abstract" in self.current_json_data:
            abstract_text = self.current_json_data["abstract"]
            print(f"Abstract Text:\n{abstract_text}")  # Debugging line
            json_doc = self.query_one("#json-document", JSONDocument)
            json_doc.load_text(abstract_text)
            json_doc.cursor_position = (0, 0) # Reset to top
        elif self.current_json_data and isinstance(self.current_json_data, dict):
            # Check for abstract in the first level values if the top level doesn't have it
            for value in self.current_json_data.values():
                if isinstance(value, dict) and "abstract" in value:
                    abstract_text = value["abstract"]
                    print(f"Abstract Text (nested):\n{abstract_text}")  # Debugging line
                    json_doc = self.query_one("#json-document", JSONDocument)
                    json_doc.load_text(abstract_text)
                    json_doc.cursor_position = (0, 0) # Reset to top
                    return


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