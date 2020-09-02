
from typing import Dict, Any
import os.path
import sys
import importlib

import click

from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.inventory import Inventory, Hosts
from nornir.core.filter import F
from nornir_rich.plugins.processors import RichResults

@click.group()
@click.option(
    '-k', '--kwargs', 
    help='Filter hosts using F'
)
@click.option(
    '-g', '--groups', 
    help='Filter hosts using groups'
)
@click.option(
    '-h', '--hosts', 
    help='Filter hosts using names'
)
@click.option(
    '-c', '--config', 
    default='config.yaml', 
    help='Nonrnir config file path'
)
@click.pass_context
def cli(ctx, kwargs, groups, hosts, config):
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
    help='Module to run including python path',
    required=True
)
@click.option(
    '-a', '--args',
    help='Arguments required by module'
)
@click.pass_context
def adhoc(ctx: click.Context, module: str, args: str):
    nr = get_nornir(ctx.parent.params['config'])
    rr = RichResults()
    nr.processors.append(rr)
    
    function = module.split('.')[-1]
    package = '.'.join(module.split('.')[:-1])
    task = getattr(importlib.import_module(package), function)

    filtered = get_filtered(nr, ctx.parent.params)
    filtered.run(
        task=task,
        **{k: v for k, v in [a.split('=') for a in args.split(',')]}
    )

def main():
    cli()

if __name__ == "__main__":
    main()