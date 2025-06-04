from __future__ import annotations
import json
from rich.highlighter import ReprHighlighter
from rich.text import Text
from rich.pretty import pretty_repr
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widget import Widget
from textual.widgets import (
    Label,
    ProgressBar,
    Tree,
    Static, 
)
from textual.widgets.tree import TreeNode
from os import get_terminal_size

highlighter = ReprHighlighter()

###############################  Tree node widgets ##############################

# Define the type hint for the tree node data
JSONNodeData = dict | list | str | int | float | bool | None

class JSONTree(Tree[JSONNodeData]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_node(self, name: str, node: TreeNode, data: object) -> None:
        """Adds a node to the tree.

        Args:
            name (str): Name of the node.
            node (TreeNode): Parent node.
            data (object): Data associated with the node.
        """
        if isinstance(data, dict):
            node.set_label(Text(f"{{}} {name}"))
            for key, value in data.items():
                new_node = node.add("")
                self.add_node(key, new_node, value)
                new_node.data = value

        elif isinstance(data, list):
            node.set_label = Text(f"{name}")
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
            node.set_label(label)
            node.data = data

# class JSONTree(Tree):

#     def add_node(self, name: str, node: TreeNode, data: object) -> None:
#         """Adds a node to the tree.

#         Args:
#             name (str): Name of the node.
#             node (TreeNode): Parent node.
#             data (object): Data associated with the node.
#         """
#         if isinstance(data, dict):
#             node._label = Text(f"{{}} {name}")
#             for key, value in data.items():
#                 new_node = node.add("")
#                 self.add_node(key, new_node, value)
#                 new_node.data = value

#         elif isinstance(data, list):
#             node._label = Text(f"{name}")
#             for index, value in enumerate(data):
#                 new_node = node.add("")
#                 self.add_node(str(index), new_node, value)
#                 new_node.data = value
#         else:
#             node._allow_expand = False
#             if name:
#                 label = Text.assemble(
#                     Text.from_markup(f"[b]{name}[/b]="), highlighter(repr(data))
#                 )
#             else:
#                 label = Text(repr(data))
#             node._label = label
#             # node.set_label(label)
#             node.data = data
            
# class TreeView(Widget, can_focus_children=True):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#     def compose(self) -> ComposeResult:
#         tree = JSONTree()
#         tree.show_root = False
#         yield tree

class TreeView(Widget, can_focus_children=True):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        
    def compose(self) -> ComposeResult:
        tree = JSONTree("Root")
        tree.show_root = False
        yield tree

#######################TabbedContent #############################

#######################Document tab Widgets #############################
class JSONDocument(ScrollableContainer):
    """Widget to display JSON data (as plain text) with scrolling.

    Args:
         JSONDocument (ScrollableContainer): Scrollable container

    Returns:
        _type_: _description_
    """    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_static = Static("", id="json-text", markup=False)

    def on_mount(self) -> None:
        """Mount the pre-created Static widget."""
        self.mount(self.json_static)

    def load(self, json_data: str | dict | list) -> bool:
        """Load JSON data and update the Static widget's content.

        Args:
            json_data (str | dict | list): _description_

        Returns:
            bool: Loads formatted json into static widget
        """        
        try:
            if isinstance(json_data, str):
                try:
                    # Attempt to parse as JSON, but don't require it
                    parsed_data = json.loads(json_data)
                    formatted_text = pretty_repr(parsed_data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, just display the raw string
                    formatted_text = json_data
            elif isinstance(json_data, (dict, list, int)):
                formatted_text = pretty_repr(json_data)
            else:
                formatted_text = f"Error: Invalid input type: {type(json_data)}"
                self.json_static.update(formatted_text) # Update existing static
                return False

            self.json_static.update(formatted_text) # Update existing static
            return True

        except Exception as e:
            formatted_text = f"An unexpected error occurred: {e}"
            # Use plain=True in update for extra safety with error messages
            self.json_static.update(formatted_text)
            return False

class JSONDocumentView(JSONDocument): #ScrollableContainer
    """Container for the JSON document.

    Args:
        JSONDocument (Widget): Inherits from the JSONDocument Class

    Yields:
        Widget : The JSONDocumentView Widget
    """

    def compose(self) -> ComposeResult:
        """Compose the JSONDocument widget."""
        yield JSONDocument(id="json-document")

    def update_document(self, json_data: str | dict | list | int) -> None:
        """Update the JSON document with new data."""
        json_doc = self.query_one("#json-document", JSONDocument)
        json_doc.load(json_data)

####################### Loading Widget #############################

#Old Widget. 
class LoadingIndicator(Static):
    """Custom loading indicator widget."""
    DEFAULT_CSS = '''
    LoadingIndicator {
        width: 40%;
        height: 60%;
        background: $boost;
        border: heavy $accent magenta;
        border-title-color: $accent white;
        padding: 1 2;
        margin: 1 1;
        content-align: center middle;
    }

    #loading-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    '''

    def __init__(self, message="Updating..."):
        super().__init__()
        self.message = message
        self.count = 0
        self.total = 0
        self.border_title = "ML_Tree"

    def update_progress(self, count, total=None):
        """Update the progress count."""
        self.count = count
        if total is not None:
            self.total = total
        self.update()

    def render(self):
        #ehhh.  mmaybe switch this to rich's actual progress bar instead of making it?  I mean its cool don't get me wrong, but why reinvent the wheel. 
        """Render the loading indicator with progress."""
        progress_text = f"{self.count} datasets"
        if self.total > 0:
            progress_percent = min(100, int((self.count / self.total) * 100))
            progress_bar = "▓" * (progress_percent // 5) + "░" * (
                20 - (progress_percent // 5)
            )
            progress_text = f"{self.count}/{self.total} datasets ({progress_percent}%)\n{progress_bar}"

        return f"[bold]{self.message}[/bold]\n\n[bold]{progress_text}[/bold]"


# ####################### Loading Widget #############################

Segment = tuple[str, str]
def ceil(a, b):
    return (a + b) // b

class SearchProgress(ProgressBar):
    """Load a progress bar for searching"""
    def __init__(self, count:int, total:int, message:str="Updating..."):
        super().__init__()
        self.message = message
        self.count = count
        self.total = total
        self.border_title = "Searching.."
        self.color = "magenta"
        self.width = round(0.8 * get_terminal_size()[0])

    # def style_text(self, segment: Segment) -> Text:
    #     return Text.from_markup(segment[0], style=self.color,) + Text.from_markup(
    #         segment[1],
    #         style="d black",
    #     )
    
    # def render_minimal(self, done, rem) -> Segment:
    #     pre = "━" * done
    #     suf = "━" * rem
    #     return pre, suf

    # def render(self) -> Text:
    #     done = round(self.count / self.total * self.width)
    #     rem = self.width - done
    #     segment = eval(f"self.render_minimal({done}, {rem})")
    #     return self.style_text(segment)

# BarStyle = Literal["minimal", "pacman", "rust", "doge", "balloon"]
####################### Search tab Widgets #############################

#NOTE - Save for Search Tab
    #You'll need a checkbox here to indicate if you want to save a search to the root node / and the data/search_results folder 
