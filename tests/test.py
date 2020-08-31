import os
import ipdb
import json
from ruamel import yaml
import subprocess
import time

from nornir import InitNornir
from nornir.core.task import Result

from nornir_rich.plugins.processors import RichResults


dir_path = os.path.dirname(os.path.realpath(__file__))

inv = InitNornir(
    runner={
        "plugin": "threaded",
        "options": {
            "num_workers": 100,
        },
    },
    inventory={
        "plugin": "SimpleInventory",
        "options": {"host_file": f"{dir_path}/test_data/hosts.yaml"},
    },
)


def gen_exception(task):
    x = 1 / 0


def other_task(task, x):
    return 1

def other_task2(task):
    time.sleep(5)

def other_task3(task):
    time.sleep(10)

def super_group(task):
    task.run(grouped_task2, x=1, name="From level 1")

def grouped_task(task, x):
    task.run(other_task, x=1, name="Run other task")

def grouped_task2(task, x):
    task.run(other_task2, name="From level 2")
    task.run(other_task3, name="othertask 3")

def return_dict(task, x):
    return {"test": "one", "other": {"x": 1, "y": 2}}

def return_json(task, x):
    return json.dumps({"test": "one", "other": {"x": 1, "y": 2}})

def return_yaml(task, x):
    return yaml.dump({"test": "one", "other": {"x": 1, "y": 2}})

def return_system(task, x):
    return subprocess.check_output(['/usr/bin/cat', '/etc/passwd'])

def return_diff(task, x):
    return open(f"{dir_path}/test_data/test.diff", "r").read()

def return_xml(task, x):
    return open(f'{dir_path}/test_data/test.xml', 'r').read()

def return_shell(task, x, y):
    return open(f"{dir_path}/test_data/shell.out", "r").read()

rr = RichResults()
#rr.write_inventory(inv)
inv.processors.append(rr)

inv.run(grouped_task2, x=1, name="Timed grouped task")
inv.run(grouped_task, x=1, name="Run grouped task")
inv.run(return_dict, x=1, name="Return dict")
inv.run(return_system, x=1, name="Return system")
inv.run(return_json, x=1, name="Return JSON")
inv.run(return_yaml, x=1, name="Return YAML")
inv.run(return_xml, x=1, name="Return XML")
inv.run(return_diff, x=1, name="Return diff")
inv.run(return_shell, x=1, name="Return shell", y={'test': 1})
inv.run(gen_exception, x=1, name="Generate exception")

rr.results_summary()
rr.write_results()
