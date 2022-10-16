# NzbDownloadsMultiUnpack

Unpacks multiple Usenet NZB downloads using the password stored in the filename, e.g. "foobar {{password}}".

## Requirements

* Python 3.8+
  * pipenv, install with `python3 -m pip install --user pipenv`


## How-To Run

1. `pipenv sync`
2. `pipenv run python multiunpackrecursive.py <BASEDIR>`
