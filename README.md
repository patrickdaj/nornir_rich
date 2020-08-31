# nornir_rich

nornir_rich is a customizable results printer for nornir.  It is more complex than the default print_result as it relies on a processor to get additional data for display.

## Features
- Customizable styles
- All results exportable to HTML or text (thanks to rich)
- Summary of execution
- Optional pretty print of inventory formatted as YAML
- Support for more result/stdout formats such as XML

## Installation
```python
poetry add nornir-rich
```
or
```
pip install nornir-rich
```

## Usage
After creating a nornir object, a RichResults object must be created and associated with the nornir object.

```python
# assumes nr = InitNornir()
from nornir_rich.plugins.processors import RichResult

rr = RichResult()
nr.processors.append(rr)
# or nr = nr.with_processor(rr)

rr.write_inventory(nr)

nr.run(do_stuff)

rr.write_summary()
rr.write_results()
```

## Custom styles