"""Process what our weblog_block_queue has.

Run every minute, sigh.
"""

import random
import subprocess
import sys
import time

import psycopg2


def main(argv):
    """Go Main Go."""
    # Sleep some to prevent a DOS
    time.sleep(random.randint(1, 10))
    myname = argv[1]
    pgconn = psycopg2.connect(
        database="mesosite",
        host="iemdb-mesosite.local",
        user="nobody",
        connect_timeout=5,
        gssencmode="disable",
    )
    cursor = pgconn.cursor()
    cursor.execute(
        "SELECT ctid, x_forwarded_for from weblog_block_queue WHERE "
        "target = %s",
        (myname,),
    )
    updated = False
    for row in cursor:
        updated = True
        with open("/etc/httpd/conf.d/blocklist", "a") as fh:
            fh.write(f"SetEnvIf X-Forwarded-For ^{row[1]}$ BlockAccess\n")
        cursor2 = pgconn.cursor()
        cursor2.execute(
            "DELETE from weblog_block_queue where ctid = %s", (row[0],)
        )
        cursor2.close()
        pgconn.commit()
    if updated:
        subprocess.call(["systemctl", "reload", "httpd"])


if __name__ == "__main__":
    main(sys.argv)
