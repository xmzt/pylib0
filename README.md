# xmzt_pylib

Base python library required by most other xmzt python projects.

**loglib5**: library to aid in output runtime diagnostic/debugging info.

**menumlib**: enumerations.

**optslib**: command-line processing and pre-fab "main()" classes.

## Stable build
```
python -m build && pip install .

## Development build (editable mode)
```
python -m pip install -e .
```

## Prerequisites
```
pacman -S python-pip python-build python-setuptools
```
