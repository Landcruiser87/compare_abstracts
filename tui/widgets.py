from __future__ import annotations
import json
from typing import Literal
from rich.highlighter import ReprHighlighter
from rich.text import Text
from rich.pretty import pretty_repr
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widget import Widget
from textual.widgets import (
    Static, 
    Tree, 
    ProgressBar,
)
from textual.widgets.tree import TreeNode
from os import get_terminal_size
from support import logger

highlighter = ReprHighlighter()

###############################  Tree node widgets ##############################

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

class LoadingIndicator(Static):
    """Custom loading indicator widget."""

    def __init__(self, message="Updating..."):
        super().__init__()
        self.message = message
        self.count = 0
        self.total = 0
        self.border_title = "ML_JTree"
        
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
        # \n\n[blink]⏳[/blink]"  -removed from end of above string as 
        # it was causing rendering weirdness. (Doubled the title border)


#?Checklist should refresh on the mount?  Or the page activation.... Probably the latter. 
    #As you sometimes will want to remove any searches
    #So i'll need the refresh to cycle over both the data/conferences and data/search_results.  



####################### Loading Widget #############################

Segment = tuple[str, str]
def ceil(a, b):
    return (a + b) // b

class SearchProgress(ProgressBar):
    """Load a progress bar for searching"""
    def __init__(self, count, total, message="Updating..."):
        super().__init__()
        self.message = message
        self.count = count
        self.total = total
        self.border_title = "Searching.."
        self.bar_style = "balloon"
        self.color = "magenta"
        self.width = round(0.8 * get_terminal_size()[0])

    # def update_progress(self, count, total=None):
    #     """Update the progress count."""
    #     self.count = count
    #     if total is not None:
    #         self.total = total
    #     self.update()
    
    def style_text(self, segment: Segment) -> Text:
        return Text.from_markup(segment[0], style=self.color,) + Text.from_markup(
            segment[1],
            style="d black",
        )
    
    def render_balloon(self, done, rem):
        total = done + rem
        bg = "⠁⠈⠐⠠⢀⡀⠄⠂"
        bg = bg * ceil(total, len(bg))
        return bg[: max(done - 1, 0)] + "🎈", bg[done : done + rem]
    
    def render(self) -> Text:
        done = round(self.count / self.total * self.width)
        rem = self.width - done
        segment = eval(f"self.render_balloon({done}, {rem})")
        return self.style_text(segment)



# BarStyle = Literal["minimal", "pacman", "rust", "doge", "balloon"]

# class SearchProgress(ProgressBar):
#     #Borrowed from here
#     # https://github.com/NL2Code/CodeS/blob/0b624ab4ef22b0d9d223f274a986eb27fe090c88/repos/termtyper-main/termtyper/ui/widgets/progress_bar.py#L14
#     def __init__(
#         self,
#         total: float,
#         completed: float,
#         bar_style: BarStyle = "minimal",
#         color: str = "white",
#     ) -> None:
#         self.total = total
#         self.completed = completed
#         self.bar_style = bar_style
#         self.color = color
#         self.width = round(0.8 * get_terminal_size()[0])

#     def style_text(self, segment: Segment) -> Text:
#         return Text.from_markup(segment[0], style=self.color,) + Text.from_markup(
#             segment[1],
#             style="d black",
#         )

#     def render_balloon(self, done, rem):
#         total = done + rem
#         bg = "⠁⠈⠐⠠⢀⡀⠄⠂"
#         bg = bg * ceil(total, len(bg))
#         return bg[: max(done - 1, 0)] + "🎈", bg[done : done + rem]

#     def render_minimal(self, done, rem) -> Segment:
#         pre = "━" * done
#         suf = "━" * rem
#         return pre, suf

#     def render_doge(self, done, rem):
#         pre = "$" * (done - 2) + " "
#         pre += "[yellow]:dog:[/yellow]"
#         suf = "━" * rem
#         suf += "🌝"
#         return pre, suf

#     def render_rust(self, done, rem) -> Segment:
#         pre = "━" * (done - 1)
#         pre += ":crab:"
#         suf = "━" * rem
#         self.color = "orange1"
#         return pre, suf

#     def render_pacman(self, done, rem) -> Segment:
#         pre = ("-" * (done - 1)) + ("c" if done % 2 else "C")
#         suf = ("● " if done % 2 else " ●") * rem
#         suf = suf[:rem]
#         return pre, suf

#     def render(self) -> Text:
#         done = round(self.completed / self.total * self.width)
#         rem = self.width - done
#         segment = eval(f"self.render_{self.bar_style}({done}, {rem})")
#         return self.style_text(segment)


####################### Search tab Widgets #############################

#NOTE - Save for Search Tab
    #You'll need a checkbox here to indicate if you want to save a search to the root node / and the data/search_results folder 
