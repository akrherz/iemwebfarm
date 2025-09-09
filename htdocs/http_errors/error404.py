"""Our custom 404 handler."""

import ipaddress
import re
import sys
from datetime import datetime, timedelta, timezone

from pyiem.database import sql_helper, with_sqlalchemy_conn
from pyiem.templates.iem import TEMPLATE
from pyiem.util import LOG, utc
from sqlalchemy.engine import Connection

IEM_VHOSTS = [
    "mesonet.agron.iastate.edu",
    "iem.local",
    "www.mesonet.agron.iastate.edu",
    "mesonet1.agron.iastate.edu",
    "mesonet2.agron.iastate.edu",
    "mesonet3.agron.iastate.edu",
    "mesonet4.agron.iastate.edu",
]
COWIMG = "https://mesonet.agron.iastate.edu/images/cow404.jpg"
ARCHIVE_RE = re.compile(
    r"^/archive/data/(\d{4})/(\d{2})/(\d{2})/(.*)_(\d{8})_?(\d{2,4})"
)
WMS_RE = re.compile("WMS", re.IGNORECASE)


# Common junk tokens that sometimes appear in X-Forwarded-For
_BAD_XFF_TOKENS = {
    "unknown",
    "null",
    "none",
    "-",
    "true",
    "false",
    "yes",
    "no",
}


def sanitize_x_forwarded_for(xff_value: str | None) -> str | None:
    """Return the first valid IP string found in X-Forwarded-For, or None.

    Handles common junk tokens, IPv4:port, and bracketed IPv6 forms.
    """
    if not xff_value:
        return None

    for raw in str(xff_value).split(","):
        token = raw.strip()
        if not token:
            continue
        if token.lower() in _BAD_XFF_TOKENS:
            continue

        ip_candidate = token

        # IPv6 with brackets: [::1]:1234 or [::1]
        if ip_candidate.startswith("[") and "]" in ip_candidate:
            ip_candidate = ip_candidate.split("]", 1)[0].lstrip("[")

        # IPv4:port -> remove trailing :port (avoid chopping IPv6)
        if (
            ":" in ip_candidate
            and ip_candidate.count(":") == 1
            and "." in ip_candidate
        ):
            ip_candidate = ip_candidate.split(":", 1)[0]

        # Strip surrounding quotes/whitespace
        ip_candidate = ip_candidate.strip().strip("'\"")

        try:
            ipaddress.ip_address(ip_candidate)
            return ip_candidate
        except ValueError:
            continue

    return None


@with_sqlalchemy_conn("mesosite")
def log_request(
    uri: str,
    environ: dict,
    redirect_status: int,
    conn: Connection | None = None,
):
    """Do some logging work."""
    snipped = f"{uri[:100]}...snipped" if len(uri) > 100 else uri
    # See mod_wsgi discussion on this
    remoteip_full = environ.get("HTTP_X_FORWARDED_FOR") or environ.get(
        "REMOTE_ADDR"
    )
    # Derive a sanitized IP from X-Forwarded-For when possible, otherwise fall
    # back to the server-provided REMOTE_ADDR value.
    remoteip = sanitize_x_forwarded_for(remoteip_full) or environ.get(
        "REMOTE_ADDR"
    )
    if redirect_status == 404:
        sys.stderr.write(
            f"404 {snipped} remote: {remoteip_full} "
            f"referer: {environ.get('HTTP_REFERER')}\n"
        )
    conn.execute(
        sql_helper(
            "INSERT into weblog(client_addr, uri, referer, http_status, "
            "x_forwarded_for, domain) VALUES (:addr, :url, :ref, :status, "
            ":xf, :domain)"
        ),
        {
            "addr": remoteip,
            "url": uri,
            "ref": environ.get("HTTP_REFERER"),
            "status": redirect_status,
            "xf": environ.get("HTTP_X_FORWARDED_FOR"),
            "domain": environ.get("HTTP_HOST"),
        },
    )
    conn.commit()


def application(environ: dict, start_response):
    """mod-wsgi handler."""
    redirect_status = int(environ.get("REDIRECT_STATUS", 404))
    http_host = environ.get("HTTP_HOST", "")
    is_iem = http_host in IEM_VHOSTS
    uri = environ.get("REQUEST_URI", "")
    # Special handling of ancient broken windrose behaviour
    if uri.startswith("/onsite/windrose/climate"):
        start_response("410 Gone", [("Content-type", "text/plain")])
        return [b"Resource is no longer available."]

    # People requesting files from the future
    m = ARCHIVE_RE.match(uri)
    if m:
        try:
            tstr = m.group(5) + m.group(6)
            fmt = "%Y%m%d%H%M" if len(tstr) == 12 else "%Y%m%d%H"
            ts = datetime.strptime(tstr, fmt).replace(tzinfo=timezone.utc)
        except Exception as exp:
            LOG.error(exp)
            ts = utc() - timedelta(days=1)
        if ts > utc():
            start_response(
                "422 Unprocessable entity", [("Content-type", "text/plain")]
            )
            return [
                b"Please adjust your script to not request files "
                b"from the future."
            ]

    # Bad WMS requests
    if WMS_RE.search(uri):
        start_response("400 Bad Request", [("Content-type", "text/plain")])
        return [
            b"This WMS url is invalid. "
            b"See https://mesonet.agron.iastate.edu/ogc/"
        ]

    try:
        log_request(uri, environ, redirect_status)
    except Exception as exp:
        sys.stderr.write(str(exp) + "\n")

    # 405s are naughty requests, which we punt them away
    if redirect_status == 405:
        start_response(
            "301 Moved Permanently", [("Location", "https://localhost")]
        )
        return [b"Moved Permanently"]

    # We should re-assert the HTTP status code that brought us here :/
    start_response("404 Not Found", [("Content-type", "text/html")])
    content = (
        "<h3>Requested file was not found</h3>"
        f'<img src="{COWIMG}" class="img img-responsive" alt="404 Cow" />'
    )
    ctx = {"title": "File Not Found (404)", "content": content}

    if is_iem:
        return [TEMPLATE.render(ctx).encode("utf-8")]
    return [content.encode("utf-8")]
