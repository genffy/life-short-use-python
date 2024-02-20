#!/bin/bash

yum install wget

wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/latest | tar -xvj bin/micromamba

./bin/micromamba shell init -s bash -p ~/micromamba
source ~/.bashrc

# activate the environment and install a new version of Python
micromamba activate
micromamba install python=3.10 -c conda-forge -y

# install the dependencies
python -m pip install -r requirements-jupyter-lite.txt

# build the JupyterLite site
jupyter lite --version
jupyter lite build --contents ipynb --output-dir dist
