"""Process what our weblog has.

Run every minute, sigh.
"""

import re
from io import StringIO

import psycopg2

# Increased from 30 as we now have a GHA workflow that will generate about
# that many :(
THRESHOLD = 40
ISU_RE = re.compile(r"^(10.90|10.24|129.186|2610:130|140.90)")
ARCHIVE_RE = re.compile(r"/archive/data/[0-9]{4}/[0-9]{2}/[0-9]{2}/")


def logic(counts: dict):
    """Should we or should we not, that is the question."""
    res = []
    for addr, hits in counts.items():
        if len(hits) < THRESHOLD or addr.startswith("127.0.0.1"):
            continue
        if ISU_RE.match(addr) is not None:
            print(f"DQ {addr}")
            continue
        # Swallow non-naughty things.
        dq = 0
        ignored = 0
        msg = StringIO()
        for hit in hits:
            # Swallow this as it is noisy
            if ARCHIVE_RE.match(hit[2]):
                ignored += 1
                continue
            if hit[2].startswith("/archive/data/"):
                dq += 1
        if ignored == len(hits):
            continue
        do_block = (len(hits) - dq) >= THRESHOLD
        msg.write(f"{addr} with {len(hits)}[{dq} DQ]/{THRESHOLD} 404s\n\n")
        for hit in hits[:10]:
            # Short circuit things
            if hit[5] == 405:
                msg.write(" scnr_engine\n")
            msg.write(
                f"{hit[0]} uri:|{hit[2]}| ref:|{hit[3]}| dom:|{hit[4]}|\n"
            )
        payload = msg.getvalue()
        # Too noisy
        if payload.find("scnr_engine") == -1:
            print(payload)
        if do_block:
            res.append(addr)
    return res


def main():
    """Go Main Go."""
    pgconn = psycopg2.connect(
        database="mesosite",
        host="iemdb-mesosite.local",
        user="nobody",
        connect_timeout=5,
        gssencmode="disable",
    )
    cursor = pgconn.cursor()
    # Anticyclone is not behind a proxy, so we have to do tricks here :/
    cursor.execute(
        "SELECT valid, coalesce(x_forwarded_for, client_addr::text), uri, "
        "referer, domain, http_status from weblog "
        "WHERE http_status in (404, 405) ORDER by valid ASC",
    )
    valid = None
    counts = {}
    for row in cursor:
        if row[1] is None or len(row[1]) < 7:
            continue
        d = counts.setdefault(row[1], [])
        d.append(row)
        valid = row[0]

    if valid is None:
        return
    cursor.execute(
        "DELETE from weblog where valid <= %s",
        (valid,),
    )
    for ip in logic(counts):
        for i in range(35, 45):
            cursor.execute(
                "INSERT into weblog_block_queue "
                "(x_forwarded_for, target) VALUES(%s, %s)",
                (ip, f"iemvs{i}-dc"),
            )
        if ip.find(",") > -1:
            ip = ip.split(",")[-1].strip()
        cursor.execute(
            "INSERT into weblog_block_queue "
            "(client_addr, target) VALUES(%s, %s)",
            (ip, "anticyclone"),
        )
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main()
