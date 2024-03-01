"""Our custom 404 handler."""

import sys

from pyiem.templates.iem import TEMPLATE
from pyiem.util import get_dbconnc

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


def log_request(uri, environ):
    """Do some logging work."""
    sys.stderr.write(
        f"404 {uri} remote: {environ.get('REMOTE_ADDR')} "
        f"referer: {environ.get('HTTP_REFERER')}\n"
    )
    pgconn, cursor = get_dbconnc("mesosite")
    cursor.execute(
        "INSERT into weblog(client_addr, uri, referer, http_status) "
        "VALUES (%s, %s, %s, %s)",
        (
            environ.get("REMOTE_ADDR"),
            uri,
            environ.get("HTTP_REFERER"),
            404,
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
