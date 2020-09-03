import os
from dotenv import load_dotenv, find_dotenv

from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get, napalm_cli
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config, netmiko_save_config, netmiko_commit

from nornir_rich.plugins.processors import RichResults


def get_password_from_env(task):
    load_dotenv(find_dotenv())
    task.host.password = os.getenv(task.host.password)

def get_interfaces(task):
    task.run(task=napalm_get, getters=["interfaces"], name="Get Vyos interfaces")

def get_environment(task):
    task.run(task=napalm_get, getters=["environment"], name="Get Vyos environment")

def run_subtasks(task):
    task.run(get_interfaces)
    task.run(get_environment)
    

nr = InitNornir(config_file="test_data/config.yaml")

rr = RichResults()
nr.processors.append(rr)

vyos = nr.filter(name="vyos")

rr.write_inventory(vyos)

vyos.run(task=get_password_from_env, name="Get password from env")
vyos.run(task=run_subtasks, name='Get Vyos info via Subtask')
vyos.run(task=netmiko_send_command, command_string='show config')
#vyos.run(task=napalm_get, getters=["interfaces"], name="Get Vyos interfaces")
#vyos.run(task=napalm_get, getters=["environment"], name="Get Vyos environment")
rr.write_summary()
