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

Current product version is 0.3.0.  `__main__.py` in the TUI folder is operational.  Currently the only two working search metrics are `Fuzzy, Cosine, and Word2vec`.  
The two search parameters that work best are `title and abstract` as those have the least amount of missing values.  (Scraping data isn't always perfect)


## Requirements
- Python >= 3.11

## Main Libraries used
- numpy
- pandas
- rich
- textual
- requests
- matplotlib
- spacy

In `VSCODE` press `CTRL + SHIFT + ~` to open a terminal
Navigate to the directory where you want to clone the repo. 

## Cloning and setting up environment.
Launch VSCode if that is IDE of choice.

# Project setup with Poetry

## How to check Poetry installation

In your terminal, navigate to your root folder.

If poetry is not installed, do so in order to continue
This will install version 2.0.0.  Adjust to your preference

On Windows
```terminal
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

On Linux/Mac
```terminal
curl -sSL https://install.python-poetry.org | python3 -
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

or 
This command will automatically activate the env
```terminal
poetry env use python3.12
```

Activate the venv
Windows
```terminal
.venv\scripts\activate
```

Mac/Linux
```terminal
source .venv/bin/activate
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
$ mkdir data/logs data/logs/scrape data/logs/tui
# mkdir data/searches 
```

## Model setup
If you'd like to use `word2vec` to do your asymetric semantic search, you'll need
to do a few things before starting.  `In your terminal, with your environment
activated` type the following in your terminal. This should install the model 
in your activated environment. You can check by looking for something like
en_core_web_md-3.8.0.... in your .venv/Lib/site-packages folder.


```terminal
python -m spacy download en_core_web_md
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
that scans the `data/conferences` folder and shows you a list of available files. 
Enter a number of the conference you want, and you're good to go.

```terminal
poetry run python tui/__main__.py

python tui/__main__.py
```

#### Runtime Notes

- Search with word2vec takes longer to run.  Patience Iago
- Fuzzy search on abstract will take even longer

Suggested operation ranges
- Fuzzy => 1 to 10
  - Best results around 5
- Cosine => -1 to 1
  - Best results around 0.40
- Word2vec => -1 to 1
  - Best results around 0.85

With the TUI running, it should look something like this. 

https://github.com/user-attachments/assets/c5b93174-1abd-43af-bd8d-d40a4c70751e


# Project Todo list

### Additional Datasets

1. Consider Arxiv API connector or BioRxiv
2. 

### Possible modeling paths

1. Implement SBert Model
2. LLM Summarization Tab
3. Clustering Tab
4. Gemma / Bert embedding
   1. tsne
   2. Look at first two components to find the subject topics that are most in variation.


### TUI
  - Tom Arnold idea.  Build a graph network from the citations of each paper
  - Analyze who is getting cited most often and driving a particular area of research.  Really like this!!
