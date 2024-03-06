<h1 align="center">
  <b>Machine Learning survey</b><br>
</h1>

<p align="center">
      <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/Python-3.8-ff69b4.svg" /></a>    
</p>


## Purpose

The purpose of this repo is to perform a yearly survey of major machine learning conferences.  Extract all the metadata, abstracts, and other information from of all the papers and look for topic frequencies that show up.  Modeling possibilities are 

1. Clustering
2. Cosine similarity to a particular subject.
3. Bert embedding into PCA.  Look at first two components to find the subject topics that are most in variation.


## Requirements
- Python >= 3.8

## Main Libraries used
- numpy
- pandas
- rich
- requests
- matplotlib

Order of operations of below terminal commands. 
- Open Terminal
- Clone repo
- Change directories
- Create venv
- Activate venv
- Install libraries

```
`CTRL + SHIFT + ~` will open a terminal
Navigate to the directory where you want to clone the repo. 

## Cloning and setting up environment.
Launch VSCode if that is IDE of choice.
 
$ git clone https://github.com/landcruiser87/compare_abstracts.git
$ cd compare_abstracts
$ python -m venv .c_venv
(Or replace ".c_venv" with whatever you want to call your environment)	

On Windows
$ .ca_venv\Scripts\activate.bat

On Mac
$ source .c_venv/bin/activate
```

Before next step, ensure you see the environment name to the left of your command prompt.  If you see it and the path file to your current directory, then the environment is activated.  If you don't activate it, and start installing things.  You'll install all the `requirements.txt` libraries into your base python environment. Which will lead to dependency problems down the road.  I promise.

![Screenshot 2023-03-28 144052](https://user-images.githubusercontent.com/16505709/228358535-3364e0ea-b273-40b8-ab59-4dddf2f92ee2.png)

```
$ pip install -r requirements.txt
```

## File Setup
While in root directory run commands below

```
$ mkdir data
$ cd data
$ mkdir logs
$ mkdir scraped
$ cd ..
```

# Project Todo list
- [ ] stuff 
- [ ] stuff stuff
- [ ] stuff stuff
- [ ] stuff stuff