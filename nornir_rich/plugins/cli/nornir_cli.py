from typing import Dict, Any, Callable
import os.path
import sys
import importlib

import click
from ruamel import yaml
from ruamel.yaml import SafeLoader

from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.inventory import Inventory, Hosts
from nornir.core.filter import F
from nornir_rich.plugins.processors import RichResults

@click.group()
@click.option(
    '-k', '--kwargs', 
    help='Filter hosts using F\n'
    + 'Example: "group__contains=group_b,group__contains=group_a"'
)
@click.option(
    '-g', '--groups', 
    help='Filter hosts using groups\n'
    + "Example: 'group_a,group_b'"
)
@click.option(
    '-h', '--hosts', 
    help='Filter hosts using names\n'
    'Example: "host_a,host_b"'
)
@click.option(
    '-c', '--config', 
    default='config.yaml', 
    help='Nonrnir config file path'
)
@click.option(
    '-o', '--options',
    help='Inventory options\n'
    + 'Example: "NB_KEY=mykey"'
)
@click.option(
    '-p', '--python',
    help='Python function that returns Nornir object'
    + "Example: 'my_nornir_stuff.get_inventory'"
)
@click.pass_context
def cli(ctx, kwargs, groups, hosts, config, options, python):
    pass

def get_nornir(config_file: str) -> Nornir:
    if os.path.exists(config_file):
        nr = InitNornir(config_file=config_file)
    else:
        sys.exit(f'{config_file} not found')

    return nr

def get_filtered(nr: Nornir, params: Dict[str, Any]) -> Nornir:
    filtered = Nornir(Inventory(hosts=Hosts()))
    filtered.processors.append(nr.processors)
    filtered.runner = nr.runner
    filtered.config = nr.config

    if not (params['hosts'] or params['groups'] or params['kwargs']):
        filtered = nr

    if params['hosts']:
        for host in params['hosts'].split(","):
            to_add = nr.filter(name=host)
            filtered.inventory.hosts.update(to_add.inventory.hosts)
    
    if params['groups']:
        for group in params['groups'].split(","):
            to_add = nr.filter(F(groups__contains=group))
            filtered.inventory.hosts.update(to_add.inventory.hosts)

    if params['kwargs']:
        for kwarg in params['kwargs'].split(","):
            f_args = dict(kwarg.split('='))
            to_add = nr.filter(F(**f_args))
            filtered.inventory.hosts.update(to_add.inventory.hosts)
    
    return filtered

@cli.command()
@click.option(
    '-p/', '--passwords',
    is_flag=True,
    help='Display passwords'
)
@click.pass_context
def inventory(ctx: click.Context, passwords: bool):
    nr = get_nornir(ctx.parent.params['config'])
    rr = RichResults()
    nr.processors.append(rr)

    filtered = get_filtered(nr, ctx.parent.params)
    rr.write_inventory(filtered, passwords=passwords)

@cli.command()
@click.option(
    '-m', '--module', 
    help='Module to run including python path\n'
    + "Example: 'nornir_utils.plugins.tasks.data.echo_data'",
    required=True
)
@click.option(
    '-a', '--args',
    help='Arguments required by module'
    + "Example: 'x=1,z=244'"
)
@click.pass_context
def adhoc(ctx: click.Context, module: str, args: str):
    nr = get_nornir(ctx.parent.params['config'])
    rr = RichResults()
    nr.processors.append(rr)
    
    task = get_task_function(module)

    filtered = get_filtered(nr, ctx.parent.params)
    filtered.run(
        task=task,
        **{k: v for k, v in [a.split('=') for a in args.split(',')]}
    )

@cli.command()
@click.option(
    'r', '--run-file',
    help='YAML file of tasks to execute'
)
@click.pass_context
def run(ctx: click.Context, run_file: str):
    if os.path.exists(run_file):
        with open(run_file, 'r') as f:
            plan = yaml.load(f.read(), Loader=SafeLoader)

    nr = get_nornir(ctx.parent.params['config'])
    rr = RichResults()
    nr.processors.append(rr)

    for sub_plan in plan:
        filtered = get_filtered(
            nr, params = {
                'hosts': sub_plan.get('hosts'),
                'groups': sub_plan.get('groups'),
                'kwargs': sub_plan.get('kwargs')
            }
        )
        
        for task in sub_plan['tasks']:
            task = get_task_function(task_list['task'])
            nr.run(task=task, name=task['name'], *task['args'], **task['kwargs'])

def get_task_function(module: str) -> Callable:
    function = module.split('.')[-1]
    package = '.'.join(module.split('.')[:-1])
    return getattr(importlib.import_module(package), function)


def main():
    cli()

if __name__ == "__main__":
    main()