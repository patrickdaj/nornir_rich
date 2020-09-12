# nornir_rich

nornir_rich is a processor/results printer for Nornir using the rich python module.

## Features
- Custom processor that supports more or less the standard Nornir format but:
    - Has progress bars built in at nornir.run level
    - Customizable styles
    - All results exportable to HTML or text (thanks to rich)
    - Summary of execution
    - Listing of inventory
    - Captures task runtime and also task details
    - Inventory output

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
from nornir_rich.plugins.functions import RichResult

rr = RichResult()

rr.inventory(nr)

rr.write(
    nr.run(do_stuff)
)

rr.summary()
rr.results()
```

The write_results automatically saves the screen output to HTML in results.html by default.