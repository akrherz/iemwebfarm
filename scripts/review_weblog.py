"""Process what our weblog has.

Run every minute, sigh.
"""
import re
import subprocess
import sys

import psycopg2

THRESHOLD = 30
MOSAIC_RE = re.compile(
    r"/archive/data/[0-9]{4}/[0-9]{2}/[0-9]{2}/"
    r"GIS/uscomp/n0[rq]_[0-9]{12}.(png|wld)"
)


def logic(counts, family):
    """Should we or should we not, that is the question."""
    exe = "iptables" if family == 4 else "ip6tables"
    res = []
    for addr, hits in counts.items():
        if len(hits) < THRESHOLD or addr == '127.0.0.1':
            continue
        # Swallow non-naughty things.
        dq = 0
        ignored = 0
        for hit in hits:
            # Swallow this as it is noisy
            if MOSAIC_RE.match(hit[2]):
                ignored += 1
                continue
            if hit[2].startswith("/archive/data/"):
                dq += 1
        if ignored == len(hits):
            continue
        do_block = (len(hits) - dq) >= THRESHOLD
        # NOTE the insert to the front of the chain
        cmd = f"/usr/sbin/{exe} -I INPUT -s {addr} -j DROP"
        print(f"{addr} with {len(hits)}[{dq} DQ]/{THRESHOLD} 404s\n{cmd}\n")
        for hit in hits[:10]:
            print(f"{hit[0]} uri:|{hit[2]}| ref:|{hit[3]}|")
        print()
        if do_block:
            subprocess.call(cmd, shell=True)
            res.append(addr)
    return res


def main(argv):
    """Go Main Go."""
    family = int(argv[1])  # either 4 or 6
    pgconn = psycopg2.connect(
        database="mesosite",
        host="iemdb-mesosite.local",
        user="nobody",
        connect_timeout=5,
        # gssencmode="disable",
    )
    cursor = pgconn.cursor()
    cursor.execute(
        "SELECT valid, client_addr, uri, referer from weblog WHERE "
        "http_status = 404 and family(client_addr) = %s ORDER by valid ASC",
        (family,),
    )
    valid = None
    counts = {}
    for row in cursor:
        d = counts.setdefault(row[1], [])
        d.append(row)
        valid = row[0]

    if valid is None:
        return
    cursor.execute(
        "DELETE from weblog where valid <= %s and family(client_addr) = %s",
        (valid, family),
    )
    for ip in logic(counts, family):
        for i in range(35, 45):
            cursor.execute(
                "INSERT into weblog_block_queue "
                "(protocol, client_addr, target) VALUES(%s, %s, %s)",
                (family, ip, f"iemvs{i}-dc")
            )
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main(sys.argv)
