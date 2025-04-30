<h1 align="center">
  <b>Machine Learning survey</b><br>
</h1>

<p align="center">
      <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/Python-3.11-ff69b4.svg" /></a>    
</p>


## Purpose

The purpose of this repo is to perform a yearly survey of major machine learning conferences.  Extract all the metadata, abstracts, and other information from of all the papers and look for topic frequencies that show up.  

## Disclaimer 

Current product version is 0.2.8.  Tui folder is currently under construction so run any TUI commands from the backup/0.2.8 folder.  

## Requirements
- Python >= 3.11

## Main Libraries used
- numpy
- pandas
- rich
- textual
- requests
- matplotlib

In `VSCODE` press `CTRL + SHIFT + ~` to open a terminal
Navigate to the directory where you want to clone the repo. 

## Cloning and setting up environment.
Launch VSCode if that is IDE of choice.

# Project setup with Poetry

## How to check Poetry installation

In your terminal, navigate to your root folder.

If poetry is not installed, do so in order to continue
This will install version 1.7.0.  Adjust to your preference

```terminal
curl -sSL https://install.python-poetry.org | python3 - --version 2.0.0
```

To check if poetry is installed on your system. Type the following into your terminal

```terminal
poetry -V
```

if you see a `version` returned, you have Poetry installed.  The second command is to update poetry if its installed. (Always a good idea). If not, follow this [link](https://python-poetry.org/docs/) and follow installation commands for your systems requirements. If on windows, we recommend the `powershell` option for easiest installation. Using pip to install poetry will lead to problems down the road and we do not recommend that option.  It needs to be installed separately from your standard python installation to manage your many python installations.  `Note: Python 2.7 is not supported`

## Environment storage

Some prefer Poetry's default storage method of storing environments in one location on your system.  The default storage are nested under the `{cache_dir}/virtualenvs`.  

If you want to store you virtual environment locally.  Set this global configuration flag below once poetry is installed.  This will now search for whatever environments you have in the root folder before trying any global versions of the environment in the cache.

```terminal
poetry config virtualenvs.in-project true
```

For general instruction as to poetry's functionality and commands, please see read through poetry's [cli documentation](https://python-poetry.org/docs/cli/)

To create a new venv

```terminal
python -m venv .venv
```

Activate the venv
Windows
```terminal
.venv\scripts\activate
```

Mac/Linux
```terminal
source .venv\bin\activate
```

To install libraries

```terminal
poetry install --no-root
```

This will read from the poetry lock file that is included
in this repo and install all necessary packagage versions.  Should other
versions be needed, the project TOML file will be utilized and packages updated according to your system requirements.  

To view the current libraries installed

```terminal
poetry show
```

To view only top level library requirements

```terminal
poetry show -T
```
## File Setup

While in root directory run commands below

```
$ cd data
$ mkdir data/logs data/logs/scrape data/logs/tui
# mkdir data/searches 
$ cd ..
```

## TUI

This repo also comes with a TUI (Terminal User Interface) that allows you to
explore the JSON objects for each conference / year.  This repo was forked from
[here](https://github.com/oleksis/jtree) and updated with a ScrollableContainer
on the right panel instead of the previous output.  Thank you to
[oleksis](https://github.com/oleksis) for creating the initial structure!! :tada:

To run the TUI with poetry
```terminal
poetry run python tui/__main__.py data/scraped/2024_ICML.json 
#replace year/conf
```

With python
```terminal
python tui/__main__.py data/scraped/2024_ICML.json 
#replace year/conf
```

With no file args, like a madman.  This will launch a file picking application
that scans the `data/scraped` folder and shows you a list of available files. 
Enter a number of the conference you want, and you're good to go.

```terminal
poetry run python tui/__main__.py

python tui/__main__.py 
```
With the TUI running, it should look something like this. 

https://github.com/user-attachments/assets/c5b93174-1abd-43af-bd8d-d40a4c70751e



# Project Todo list

### Possible modeling paths
1. Clustering
2. Gemma / Bert embedding
   1. tsne
   2. Look at first two components to find the subject topics that are most in variation.


### TUI
  - Tom Arnold idea.  Build a graph network from the citations of each paper
  - Analyze who is getting cited most often and driving a particular area of research.  Really like this!!
