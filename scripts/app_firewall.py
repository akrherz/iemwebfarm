"""Manage the iemwebfarm app firewall."""

import os
import subprocess
import sys

import click

TEXT_SOURCE = "/etc/httpd/conf.d/blocklist.txt"
DBM_OUTPUT = "/etc/httpd/conf.d/blocklist.map"
INTERACTIVE = sys.stdout.isatty()


def rebuild_dbm():
    """Compiles the text file into a DBM map for Apache."""
    try:
        # IMPORTANT, httxt2dbm upserts, so need to write a temp file and then
        # overwrite the old.
        tmpfn = "/tmp/blocklist.txt"
        subprocess.run(
            ["/usr/bin/httxt2dbm", "-i", TEXT_SOURCE, "-o", tmpfn],
            check=True,
        )
        # Move the temp file to the final destination
        os.replace(tmpfn, DBM_OUTPUT)
        # Ensure Apache can read it
        os.chmod(DBM_OUTPUT, 0o644)
        if INTERACTIVE:
            click.secho("Successfully rebuilt Apache DBM map.", fg="green")
    except Exception as e:
        click.secho(f"Error rebuilding DBM: {e}", fg="red")


@click.group()
def cli():
    """IEM Application Firewall Manager"""


@cli.command()
@click.argument("ip")
def add(ip):
    """Add an IP to the blocklist."""
    entries = set()
    if os.path.exists(TEXT_SOURCE):
        with open(TEXT_SOURCE, "r") as f:
            entries = {line.strip() for line in f if line.strip()}

    entries.add(f"{ip} BAD")

    with open(TEXT_SOURCE, "w") as f:
        f.write("\n".join(sorted(entries)) + "\n")

    if INTERACTIVE:
        click.echo(f"Added {ip} to source list.")
    rebuild_dbm()


@cli.command()
@click.argument("ip")
def remove(ip):
    """Remove an IP from the blocklist."""
    if not os.path.exists(TEXT_SOURCE):
        click.echo("Source file does not exist.")
        return

    with open(TEXT_SOURCE, "r") as f:
        lines = f.readlines()

    # Filter out the IP
    new_lines = [line for line in lines if not line.startswith(f"{ip} ")]

    if len(lines) == len(new_lines):
        click.echo(f"IP {ip} was not found in the list.")
    else:
        with open(TEXT_SOURCE, "w") as f:
            f.writelines(new_lines)
        click.echo(f"Removed {ip} from source list.")
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
