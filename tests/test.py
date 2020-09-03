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
    runner={"plugin": "threaded", "options": {"num_workers": 100,},},
    inventory={
        "plugin": "SimpleInventory",
        "options": {"host_file": f"{dir_path}/test_data/hosts.yaml"},
    },
)


def gen_exception(task):
    time.sleep(0.5)
    x = 1 / 0


def return_xml(task, x):
    time.sleep(0.5)
    return open(f"{dir_path}/test_data/test.xml", "r").read()


def return_json(task, x):
    time.sleep(0.5)
    return open(f"{dir_path}/test_data/test.json", "r").read()


def return_yaml(task, x):
    time.sleep(0.5)
    return open(f"{dir_path}/test_data/test.yaml", "r").read()


def return_diff(task, x):
    time.sleep(0.5)
    return open(f"{dir_path}/test_data/test.diff", "r").read()

def return_router_diff(task, x):
    time.sleep(0.5)
    return open(f"{dir_path}/test_data/router.diff", "r").read()

def return_router_config(task, x):
    time.sleep(0.5)
    return open(f"{dir_path}/test_data/router.config", "r").read()

def return_etree(task):
    time.sleep(0.5)
    import xml.etree.ElementTree as etree
    root = etree.Element('root')
    sub = etree.SubElement(root, 'sub')
    return root

rr = RichResults(attrib_highlight=False)
rr.write_inventory(inv)
inv.processors.append(rr)

lh = inv.filter(name="localhost")

lh.run(return_json, x=1, name="Return JSON")
lh.run(return_yaml, x=1, name="Return YAML")
lh.run(return_xml, x=1, name="Return XML")
lh.run(return_diff, x=1, name="Return Diff")
lh.run(return_router_diff, x=1, name="Return Router Diff")
lh.run(return_router_config, x=1, name="Return Router Config")
lh.run(return_etree, name="Return etree")
lh.run(gen_exception, x=1, name="Generate exception")

rr.write_summary()
rr.write_results()
