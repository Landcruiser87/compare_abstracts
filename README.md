<h1 align="center">
  <b>Machine Learning survey</b><br>
</h1>

<p align="center">
      <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/Python-3.8-ff69b4.svg" /></a>    
</p>


## Purpose

The purpose of this repo is to perform a yearly survey of major machine learning conferences.  Extract all the metadata, abstracts, and other information from of all the papers and look for topic frequencies that show up.  

1. Clustering
2. Cosine similarity to a particular subject.
3. Bert embedding into PCA.  Look at first two components to find the subject topics that are most in variation.

## Requirements
- Python >= 3.11

## Main Libraries used
- numpy
- pandas
- rich
- textual
- requests
- matplotlib

Order of operations of below terminal commands. 
- Open Terminal
- Clone repo
- Change directories
- Create venv
- Activate venv
- Install libraries

`CTRL + SHIFT + ~` will open a terminal
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


## Environment storage
## File Setup

While in root directory run commands below

```
$ cd data
$ mkdir logs
$ mkdir screenshots
$ cd ..
```

## TUI

This repo also comes with a TUI (Terminal User Interface) that allows you to explore the scraped JSON objects for each year.  To run the TUI with poetry

```terminal
poetry run python tui/__main__.py data/scraped/2024_ICML.json 
#replace year/conf
```


# Project Todo list
