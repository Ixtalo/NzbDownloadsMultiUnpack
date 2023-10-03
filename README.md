# NzbDownloadsMultiUnpack

Unpacks multiple Usenet NZB downloads using the password stored in
the file/folder name, e.g. ".../foobar {{password}}/somearchive.rar".

## Requirements

* Python 3.8+
  * pipenv, install with `python3 -m pip install --update --user pipenv`


## How-To Run

1. `pipenv sync`
2. `pipenv run python multiunpackrecursive.py <BASEDIR> > unpack_delete.sh`
3. check `unpack_delete.sh`
4. `bash unpack_delete.sh`
