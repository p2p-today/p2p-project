from __future__ import print_function

import click

from sys import argv
from time import sleep

from . import bootstrap
from .chord import ChordSocket, Protocol

verbosity = 0
seed_nodes = {}


@click.group()
@click.option('-v', '--verbose', count=True)
def cli(verbose=0):
    verbosity = verbose
    click.echo('Verbosity mode is {}'.format(verbosity))


@cli.command()
@click.option('--transport', default='TCP', type=click.Choice(('TCP', 'SSL')))
@click.option('--outward_address', type=str)
@click.option('--outward_port', type=int)
@click.option('--address', type=str, default='0.0.0.0')
@click.option('--port', type=int, default=44565)
def seed(transport=None, outward_port=None, outward_address=None, port=None, address=None):
    transport = {
    'TCP': 'Plaintext',
    'SSL': 'SSL'
    }[transport]
    if transport not in seed_nodes:
        kwargs = {
            'addr': address,
            'port': port,
            'proto': Protocol('bootstrap', transport)
        }
        if outward_address and outward_port:
            kwargs['out_addr'] = (outward_address, outward_port)
        seed_nodes[transport] = bootstrap(ChordSocket, **kwargs)
        seed_nodes[transport].join()


def main():
    try:
        cli(prog_name='py2p')
    except SystemExit:
        if 'seed' not in argv:
            raise

    click.echo("Seeding the bootstrap network on:")
    for transport, node in seed_nodes.items():
        click.echo("\t- {} ({}:{})".format(transport, *node.addr))

    try:
        while True:
            sleep(100)
    except:
        click.echo("Shutting down...")
        for node in seed_nodes.values():
            node.unjoin()
            node.close()


if __name__ == '__main__':
    main()
