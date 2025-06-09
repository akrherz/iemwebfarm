"""Process what our weblog_block_queue has.

Run every minute, sigh.
"""

import random
import subprocess
import sys
import time
from datetime import datetime, timezone

import psycopg


def main(argv):
    """Go Main Go."""
    # Sleep some to prevent a DOS
    time.sleep(random.randint(1, 10))
    myname = argv[1]
    pgconn = psycopg.connect(
        dbname="mesosite",
        host="iemdb-mesosite.local",
        user="nobody",
        connect_timeout=5,
        gssencmode="disable",
    )
    cursor = pgconn.cursor()
    cursor.execute(
        "SELECT ctid, x_forwarded_for, banned from weblog_block_queue WHERE "
        "target = %s",
        (myname,),
    )
    newlines = []
    bannedlines = []
    for row in cursor:
        # We need to escape the periods
        xff = row[1].replace(".", r"\.").split("/")[0]
        ss = f"# {datetime.now(timezone.utc).isoformat()}"
        (bannedlines if row[2] else newlines).append(
            f'SetEnvIf X-Forwarded-For "^{xff}$" BlockAccess=1  {ss}\n'
        )
        cursor2 = pgconn.cursor()
        cursor2.execute(
            "DELETE from weblog_block_queue where ctid = %s", (row[0],)
        )
        cursor2.close()
        pgconn.commit()
    if newlines:
        with open("/etc/httpd/conf.d/blocklist") as fh:
            lines = fh.readlines()
        lines.extend(newlines)
        with open("/etc/httpd/conf.d/blocklist", "w") as fh:
            fh.write("".join(lines[-100:]))
    if bannedlines:
        with open("/etc/httpd/conf.d/banlist") as fh:
            lines = fh.readlines()
        lines.extend(bannedlines)
        with open("/etc/httpd/conf.d/banlist", "w") as fh:
            fh.write("".join(lines))
    if newlines or bannedlines:
        subprocess.call(["systemctl", "reload", "httpd"])


if __name__ == "__main__":
    main(sys.argv)
