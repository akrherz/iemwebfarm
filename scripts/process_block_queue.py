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
    )
    cursor = pgconn.cursor()
    cursor.execute(
        "SELECT ctid, protocol, client_addr from weblog_block_queue WHERE "
        "target = %s",
        (myname,),
    )
    for row in cursor:
        exe = "iptables" if row[1] == 4 else "ip6tables"
        cmd = [
            f"/usr/sbin/{exe}",
            "-I",
            "INPUT",
            "-s",
            row[2],
            "-j",
            "DROP",
        ]
        subprocess.call(cmd)
        cursor2 = pgconn.cursor()
        cursor2.execute(
            "DELETE from weblog_block_queue where ctid = %s", (row[0],)
        )
        cursor2.close()
        pgconn.commit()


if __name__ == "__main__":
    main(sys.argv)
