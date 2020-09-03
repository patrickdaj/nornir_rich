# nornir_rich

nornir_rich is a set of CLI tools for Nornir.  Maybe it should be named nornir-clitools. :)

## Features
- Custom processor that supports more or less the standard Nornir format but:
    - Has progress bars built in at nornir.run level
    - Customizable styles
    - All results exportable to HTML or text (thanks to rich)
    - Summary of execution
    - Listing of inventory
    - Captures task runtime and also task details (nothing done with task details yet)
- Inventory output in processor and CLI (similar to anisble-inventory)
- Adhoc run task in CLI (similar to ansible-adhoc)
- Support for running tasks from YAML (similar to ansible-playbook)

## Demo
[![asciicast](https://asciinema.org/a/04Xpc2MybxqVkrEhCgA9K39Wr.svg)](https://asciinema.org/a/04Xpc2MybxqVkrEhCgA9K39Wr)


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

The write_results automatically saves the screen output to HTML in results.html by default.

## Debugging with step and start_at

# nornir-cli

## Inventory with nornir-cli inventory

## Run addhoc tasks with nornir-cli adhoc

## Be like an ansible with nornir-cli run and still have a debugger
