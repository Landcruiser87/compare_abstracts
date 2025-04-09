from __future__ import annotations
import json
from rich.highlighter import ReprHighlighter
# from rich.syntax import Syntax
from rich.text import Text
from rich.pretty import pretty_repr
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widget import Widget
from textual.widgets import (
    Static, 
    Tree, 
    SelectionList
)
from textual.widgets.tree import TreeNode
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

#######################TabbedContent Widgets #############################

#######################Content tab  Widgets #############################
class JSONDocument(ScrollableContainer):
    """Widget to display JSON data (as plain text) with scrolling.

    Args:
         JSONDocument (ScrollableContainer): Scrollable container

    Returns:
        _type_: _description_
    """    

    DEFAULT_CSS = """
    JSONDocument {
        width: 1fr;
        height: 1fr;
    }
    JSONDocument Static {
        width: 100%;
        height: auto;
        padding: 1 2;
    }
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
    DEFAULT_CSS = """
       JSONDocumentView {
           height: 1fr;
           width: 1fr;
       }
       """

    def compose(self) -> ComposeResult:
        """Compose the JSONDocument widget."""
        yield JSONDocument(id="json-document")

    def update_document(self, json_data: str | dict | list | int) -> None:
        """Update the JSON document with new data."""
        json_doc = self.query_one("#json-document", JSONDocument)
        json_doc.load(json_data)

####################### Dataset tab  Widgets #############################

# class DatasetList(SelectionList): 
#     """Container for the JSON document.

#     Args:
#         DatasetList (Widget): Inherits from the SelectionList Class

#     Yields:
#         Widget : The SelectionList Widget
#     """    
#     # DEFAULT_CSS = """
#     #    JSONDocumentView {
#     #        height: 1fr;
#     #        width: 1fr;
#     #    }
#     #    """

#     def compose(self) -> ComposeResult:
#         """Compose the JSONDocument widget."""
#         yield SelectionList(id="json-document")

    #NOTE - Not sure if i need this. 


#TODO - Add Dataset button
#TODO - Remove Dataset Button
#TODO - Dataset checklist 

#Main functionality is that when you press the add dataset.  It cycles through the checklist object and 
#adds those datasets to the root node. Subtract does the opposite.  

#Checklist should refresh on the mount?  Or the page activation.... Probably the latter. 
    #As you sometimes will want to remove any searches
    #So i'll need the refresh to cycle over both the data/conferences and data/search_results.  



####################### Search tab Widgets #############################

#NOTE - Save for Search Tab
    #You'll need a checkbox here to indicate if you want to save a search to the root node / and the data/search_results folder 
