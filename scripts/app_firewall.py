"""Manage the iemwebfarm app firewall."""

import os
import subprocess
import sys
from datetime import datetime, timezone

import click

TEXT_SOURCE = "/mesonet/blocklist.txt"
DBM_OUTPUT = "/mesonet/blocklist.map"
INTERACTIVE = sys.stdout.isatty()


def rebuild_dbm():
    """Compiles the text file into a DBM map for Apache."""
    try:
        # IMPORTANT, httxt2dbm upserts
        subprocess.run(
            ["/usr/bin/httxt2dbm", "-i", TEXT_SOURCE, "-o", DBM_OUTPUT],
            check=True,
        )
        # Ensure Apache can read it
        os.chmod(DBM_OUTPUT, 0o644)
        if INTERACTIVE:
            click.secho("Successfully rebuilt Apache DBM map.", fg="green")
    except Exception as e:
        click.secho(f"Error rebuilding DBM: {e}", fg="red")


def set_ip(ip: str, newval: str) -> bool:
    """Update or insert the text file with the new entry."""
    new_lines = []
    found = False
    if os.path.isfile(TEXT_SOURCE):
        with open(TEXT_SOURCE, "r") as f:
            # retains line endings...
            old_lines = f.readlines()
        for line in old_lines:
            if line.startswith(f"{ip} "):
                found = True
                new_lines.append(f"{ip} {newval}\n")
            else:
                new_lines.append(line)
    with open(TEXT_SOURCE, "w") as f:
        f.writelines(new_lines)
    return found


@click.group()
def cli():
    """IEM Application Firewall Manager"""


@cli.command()
@click.argument("ip")
def block(ip):
    """Add an IP to the blocklist."""
    set_ip(ip, "BAD")

    if INTERACTIVE:
        click.echo(f"Added {ip} to source list.")
    rebuild_dbm()


@cli.command()
@click.argument("ip")
def unblock(ip):
    """Remove an IP from the blocklist."""
    utcnow = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = set_ip(ip, utcnow)

    if not found:
        click.echo(f"IP {ip} was not found in the list.")
    else:
        click.echo(f"Reset {ip} in blocklist.")
        rebuild_dbm()


@cli.command()
def list_ips():
    """Show currently blocked IPs in the text source."""
    if os.path.exists(TEXT_SOURCE):
        with open(TEXT_SOURCE, "r") as f:
            click.echo(f.read())
    else:
        click.echo("Blocklist is empty.")


if __name__ == "__main__":
    # Ensure we are not root
    if os.geteuid() == 0:
        click.secho("This script should not be run as root.", fg="red")
        sys.exit(1)
    cli()
