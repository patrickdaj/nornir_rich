import os
from dotenv import load_dotenv, find_dotenv

from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get, napalm_cli

from nornir_rich.plugins.processors import RichResults


def get_password_from_env(task):
    load_dotenv(find_dotenv())
    task.host.password = os.getenv(task.host.password)


nr = InitNornir(
    inventory={
        "plugin": "SimpleInventory",
        "options": {
            "host_file": "test_data/hosts.yaml",
            "defaults_file": "test_data/defaults.yaml",
        },
    },
    dry_run=True,
)

rr = RichResults()
nr.processors.append(rr)

vyos = nr.filter(name="vyos")

vyos.run(task=get_password_from_env, name="Get password from env")
vyos.run(task=napalm_get, getters=["interfaces"], name="Get Vyos interfaces")
vyos.run(task=napalm_get, getters=["environment"], name="Get Vyos environment")
vyos.run(
    task=napalm_cli, commands=["show configuration"], name="Get Vyos configuration"
)
rr.write_summary()
