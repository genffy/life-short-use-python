# life-short-use-python

just a test

## venv
⚠️ deprecated: move to conda
```shell
python -m venv ./venv
source ./venv/bin/activate
```

## dev
### install pkg
```shell
# single
python -m pip install <pkg-name>
# multi
python -m pip install -r requirements.txt
````

### update requirements
```shell
python -m pip freeze > requirements.txt
```

### pre-commmit check
[pre-commit](https://pre-commit.com/#install )
```shell
pre-commit install
pre-commit run --all-files
```
