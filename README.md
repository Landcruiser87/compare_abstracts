<h1 align="center">
  <b>Machine Learning survey</b><br>
</h1>

<p align="center">
      <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/Python-3.11-ff69b4.svg" /></a>    
</p>


## Purpose

The purpose of this repo is to perform a yearly survey of major machine learning conferences and arXiv.  Extract all the metadata, abstracts, and other information from of all the papers and look for topic frequencies that show up.  

## Disclaimer 

Current product version is 0.3.0.  `__main__.py` in the TUI folder is operational.  Currently the only two working search models are `Fuzzy, Cosine, Word2vec, Marco and Specter`.  
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
- scikit-learn
- beautifulsoup4
- pyzotero (eventually)

In `VSCODE` press `CTRL + SHIFT + ~` to open a terminal
Navigate to the directory where you want to clone the repo. 

## Cloning and setting up environment.
Launch VSCode if that is IDE of choice.

# Project setup with Poetry

## How to check Poetry installation

In your terminal, navigate to your root folder.

If poetry is not installed, do so in order to continue.

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

if you see a `version` returned, you have Poetry installed.  The second command is to update poetry if its installed. (Always a good idea). If not, follow this [link](https://python-poetry.org/docs/) and follow installation commands for your systems requirements. If on windows, we recommend the `powershell` option for easiest installation. Using pip to install poetry will lead to problems down the road and we do not recommend that option.  It needs to be installed separately from your standard python installation to manage your many python installations.  `Note: Python 2.7 is not supported`.  You are more than welcome to go the pip route but I can't guarantee your dependencies won't clash.

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

### Installation with GPU
To use your GPU, or not to use your GPU.  That is the question.  If you're lucky enough to have workhorse GPU on your rig, you might be inclined to use it when selecting the "Marco" and "Specter" models.  To do so requires... a few extra annoying steps.  Hopefully you bought into the NVIDIA hype and have one of their GPU's as most of pytorch's implmentations are based on the NVIDIA CUDA drivers.  

First order of business is to see what NVIDIA drivers you can currently operate at.  

```terminal
nvidia-smi
```

After running the above look on the top right for `CUDA Version: xx.x`
This will be the maximum CUDA version you can use with your current installation. If you want to install pytorch, you'll need to install a CUDA toolkit that is `BELOW` that max version.  If you go over it... well that's on you.  

Now you'll need to head over to 
[pytorchs getting started page](https://pytorch.org/get-started/locally/)

Go through the selections and see which align with your system.  My only options were 11.8 or 12.6.  Since my NVIDIA max driver version is 12.5.  11.8 it is!  Because poetry is a bit extra, we'll have to add the source for whatever cuda version will fit below your GPU's current NVIDIA drivers.  

```terminal
poetry source add --priority=explicit pytorch-cuda "https://download.pytorch.org/whl/cu118"
```

After the source is added, you should see something like this in your project.toml file.

```
[[tool.poetry.source]]
name = "pytorch-cuda"
url = "https://download.pytorch.org/whl/cu118"
priority = "explicit"
```

Now you can install the specific versions of what you'll need to run SBert models on your GPU. In my case, these were the available versions from the 11.8 CUDA Toolkit.

```terminal
poetry add torch==2.7.0+cu118 torchaudio==2.7.0+cu118 torchvision==0.22.0+cu118 --source pytorch-cuda
poetry add sentence-transformers
```

### Installation without GPU

You'll want to go into the project.toml file and before you run the command below.  Delete lines `23-25` and `34-44`. Then run the following below.  To update the lock file (first) then install libraries.  Do the following

```terminal
poetry lock
poetry install --no-root
```

This will read from the project.toml file that is included in this repo and install all necessary packagage versions.  Should other versions be needed, the project TOML file will be utilized and packages updated according to your system requirements. To view the current libraries installed

```terminal
poetry show
```

To view only top level library requirements

```terminal
poetry show -T
```

## File Setup

While in root directory run commands below

```terminal
$ mkdir data/logs data/logs/scrape data/logs/tui
$ mkdir data/searches data/models/marco data/models/specter
```

## Model setup
If you'd like to use `word2vec` to do your asymetric semantic search, you'll need to do a few things before starting.  `In your terminal, with your environment activated` type the following in your terminal. This should install the model in your activated environment. You can check by looking for something like en_core_web_md-3.8.0.... in your .venv/Lib/site-packages folder.


```terminal
python -m spacy download en_core_web_md
```

## TUI

This repo also comes with a TUI (Terminal User Interface) that allows you to explore the JSON objects for each conference / year.  This repo was forked from [here](https://github.com/oleksis/jtree).  Thank you to [oleksis](https://github.com/oleksis) for creating the initial structure!! :tada:

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

With no file args, like a madman.  This will launch a file picking application that scans the `data/conferences` folder and shows you a list of available files. Enter a number of the conference you want, and you're good to go.

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
- Marco => -1 to 1
  - Best results around 0.85
- Specter => -1 to 1
  - Best results around 0.85

With the TUI running, it should look something like this. 

https://github.com/user-attachments/assets/c5b93174-1abd-43af-bd8d-d40a4c70751e


# Project Todo list

### Search Tab - Modeling paths 

[x] - Implement SBert Model
[x] - Install CUDA toolkit to use GPU
  [x] - Update instructions on how to do that


### Additional Tab's to add

1. [x] arXiv
2. medarXiv / bioarXiv
3. PubMed
4. Local Zotero search

### medarxiv / bioarxiv Tab

1. Workflow
  - Unsure at the current moment
  - Likely a checkbox that can switch maybe between medarxiv and bioarxiv
  - I think they have different inputs

### Zotero Tab

### Possible Features
1. LLM Summarization Paper Summarization
  - I bet gemini would be a good free use case
2. Clustering Tab
3. Gemma / Bert embedding
   - Tsne
   - Look at first two components to find the subject topics that are most in variation.
4. Tom Arnold idea.  Build a graph network from the citations of each paper
  - Analyze who is getting cited most often and driving a particular area of research.  Really like this!!
5. Nate Idea. Summarize each year (or current datasets) to display top 'keywords' or 'hottest categories'.
