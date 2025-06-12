"""Our custom 404 handler."""

import re
import sys
from datetime import datetime, timedelta, timezone

from pyiem.database import get_dbconnc
from pyiem.templates.iem import TEMPLATE
from pyiem.util import LOG, utc

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
    "^/archive/data/(\d{4})/(\d{2})/(\d{2})/(.*)_(\d{8})_?(\d{2,4})"
)
WMS_RE = re.compile("WMS", re.IGNORECASE)


def log_request(uri, environ):
    """Do some logging work."""
    snipped = f"{uri[:100]}...snipped" if len(uri) > 100 else uri
    # See mod_wsgi discussion on this
    remoteip_full = environ.get(
        "HTTP_X_FORWARDED_FOR", environ.get("REMOTE_ADDR")
    )
    remoteip = remoteip_full
    if remoteip_full.find(",") > 0:
        # Eh
        remoteip = remoteip.split(",")[0]
    sys.stderr.write(
        f"404 {snipped} remote: {remoteip_full} "
        f"referer: {environ.get('HTTP_REFERER')}\n"
    )
    pgconn, cursor = get_dbconnc("mesosite")
    cursor.execute(
        "INSERT into weblog(client_addr, uri, referer, http_status, "
        "x_forwarded_for, domain) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            remoteip,
            uri,
            environ.get("HTTP_REFERER"),
            404,
            environ.get("HTTP_X_FORWARDED_FOR"),
            environ.get("HTTP_HOST"),
        ),
    )
    cursor.close()
    pgconn.commit()
    pgconn.close()


def application(environ, start_response):
    """mod-wsgi handler."""
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

    # We should re-assert the HTTP status code that brought us here :/
    start_response("404 Not Found", [("Content-type", "text/html")])
    content = (
        "<h3>Requested file was not found</h3>"
        f'<img src="{COWIMG}" class="img img-responsive" alt="404 Cow" />'
    )
    ctx = {"title": "File Not Found (404)", "content": content}
    try:
        log_request(uri, environ)
    except Exception as exp:
        sys.stderr.write(str(exp) + "\n")

    if is_iem:
        return [TEMPLATE.render(ctx).encode("utf-8")]
    return [content.encode("utf-8")]
