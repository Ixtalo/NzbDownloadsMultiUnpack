# NzbDownloadsMultiUnpack

Unpacks multiple Usenet NZB downloads using the password stored in
the file/folder name, e.g. ".../foobar {{password}}/somearchive.rar".

## Requirements

* Python 3.10+
* Poetry (see https://python-poetry.org/docs/#installation)


## Usage

1. setup: `poetry install --only=main`
2. `poetry run python multiunpackrecursive.py <BASEDIR> > unpack_delete.sh`
3. check `unpack_delete.sh`
4. `bash unpack_delete.sh`
