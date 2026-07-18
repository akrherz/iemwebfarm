"""Process what our weblog has.

Run every minute, sigh.
"""

import re
import subprocess
from io import StringIO

import psycopg2

# Increased from 30 as we now have a GHA workflow that will generate about
# that many :(
THRESHOLD = 40
ISU_RE = re.compile(r"^(10.90|10.24|129.186|2610:130|140.90)")
ARCHIVE_RE = re.compile(r"/archive/data/[0-9]{4}/[0-9]{2}/[0-9]{2}/")


def should_block(addr: str, hits: list[tuple]) -> bool:
    """Should we or should we not, that is the question."""
    # Ensure if the first localhost is possible, but alas
    if len(hits) < THRESHOLD or addr in ("127.0.0.1", "127.0.0.1/32"):
        return False
    if ISU_RE.match(addr) is not None:
        print(f"DQ {addr}")
        return False
    # Now we evaluate if this IP should get blocked and if the hits
    # are interesting enough to email to the developer to review
    bad_requests = 0
    # We have a higher tolerance for these, but we only have so much
    provisional_requests = 0
    msg = StringIO()
    msg.write(f"{addr} with {len(hits)} bad requests\n\n")
    for i, hit in enumerate(hits):
        uri: str = hit[2]
        # Swallow this as it is noisy
        if ARCHIVE_RE.match(uri):
            continue
        if uri.startswith("/archive/data/"):
            provisional_requests += 1
            continue
        # OK, we have determined this one was bad
        bad_requests += 1
        # but now is this request worth logging
        if "scnr_engine" in uri or uri.startswith("/.") or hit[5] == 405:
            continue
        if i < 10:
            msg.write(f"{hit[0]} uri:|{uri}| ref:|{hit[3]}| dom:|{hit[4]}|\n")

    # Now we evaluate
    if bad_requests < THRESHOLD:
        return False

    print(msg.getvalue())
    return True


def build_counts() -> dict[str, list[tuple]]:
    """See what the database holds"""
    pgconn = psycopg2.connect(
        database="mesosite",
        host="iemdb-mesosite.local",
        user="nobody",
        connect_timeout=5,
        gssencmode="disable",
    )
    cursor = pgconn.cursor()
    cursor.execute(
        "SELECT valid, client_addr, uri, "
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

    if valid is not None:
        cursor.execute(
            "DELETE from weblog where valid <= %s",
            (valid,),
        )
        cursor.close()
        pgconn.commit()
    pgconn.close()
    return counts


def main():
    """Go Main Go."""
    counts = build_counts()

    for ip, hits in counts.items():
        if not should_block(ip, hits):
            continue
        try:
            subprocess.run(
                [
                    "/usr/bin/bash",
                    "/opt/iemwebfarm/scripts/block.sh",
                    "block",
                    ip,
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            continue


if __name__ == "__main__":
    main()
