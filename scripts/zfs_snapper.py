"""Manage some ZFS snapshots.

Hourly for a day
Daily for a week
Monthly for 6 months.

"""
import datetime
import subprocess
import sys


def magic(zvol, snap_to_make, snap_to_delete):
    """East of the Rockies, Hello."""
    cmd = ["/usr/sbin/zfs", "snapshot", f"{zvol}@{snap_to_make}"]
    subprocess.call(cmd)
    cmd = ["/usr/sbin/zfs", "destroy", f"{zvol}@{snap_to_delete}"]
    subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def main(argv):
    """Do the magic."""
    zvol = argv[1]
    now = datetime.datetime.now(datetime.timezone.utc)
    # Hourly
    magic(
        zvol,
        f"{now:%Y%m%d%H}",
        f"{(now - datetime.timedelta(hours=24)):%Y%m%d%H}",
    )
    # Daily
    if now.hour == 0:
        magic(
            zvol,
            f"{now:%Y%m%d}",
            f"{(now - datetime.timedelta(days=7)):%Y%m%d}",
        )
    # Monthly, hacky
    if now.day == 15 and now.hour == 0:
        magic(
            zvol, f"{now:%Y%m}", f"{(now - datetime.timedelta(days=183)):%Y%m}"
        )


if __name__ == "__main__":
    main(sys.argv)
