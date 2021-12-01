# `serialj`

This Python package allows to parse JSON serialized [MARC](http://format.gbv.de/marc/json) and [PICA](http://format.gbv.de/pica/json) data.

## Installation

```sh
# ... via SSH:
pip install -e git+ssh://git@github.com/herreio/serialj.git#egg=serialj
# ... or via HTTPS:
pip install -e git+https://github.com/herreio/serialj.git#egg=serialj
```

## Usage Example

```py
import json
import serialj
import urllib.request
# MARC
connection = urllib.request.urlopen("https://unapi.k10plus.de/?format=marcjson&id=opac-de-627:ppn:84738084X")
marc_raw = json.loads(connection.read().decode("UTF-8"))
connection.close()
marc_parsed = serialj.MarcJson(marc_raw)
# PICA
connection = urllib.request.urlopen("https://unapi.k10plus.de/?format=picajson&id=opac-de-627:ppn:84738084X")
pica_raw = json.loads(connection.read().decode("UTF-8"))
connection.close()
pica_parsed = serialj.PicaJson(pica_raw)
```
