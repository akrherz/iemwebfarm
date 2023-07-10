"""Apache configuration processing.

Attempts to use vanilla python.
"""
import os
import socket

APACHECONF = "/etc/httpd/conf.d"
THISREPO = "/opt/iemwebfarm"
# Straight symlinks with no template modification
SYMLINKS = [
    # https://datateam.agron.iastate.edu
    ["/opt/datateam/config/datateam.inc"],
    ["/opt/datateam/config/datateam-vhost.conf", "datateam.conf"],
    ["/opt/datateam/config/datateam_secrets.inc"],
    # https://mesonet.agron.iastate.edu
    ["/opt/iem/config/00iem.conf"],
    ["/opt/iem/config/00iem-ssl.conf"],
    ["/opt/iem/config/mesonet.inc"],
    # http://iem-backend.local
    ["/opt/iem/config/backend.conf"],
    # https://iem-archive.local
    ["/opt/iem/config/iem-archive.conf"],
    # https://mesonet-dep.agron.iastate.edu
    ["/opt/depbackend/config/apache-vhost.conf", "depbackend.conf"],
    # https://weather.im
    ["/opt/weather.im/config/weather-im-vhost.conf"],
    # https://sustainablecorn.org
    ["/opt/sustainablecorn/config/apache-vhost.conf", "sustainablecorn.conf"],
    # https://iowa.cocorahs.org
    ["/opt/cocorahs/config/apache-vhost.conf", "cocorahs.conf"],
    # https://drainagedata.org
    ["/opt/datateam/config/drainagedata-vhost.conf"],
    # virtual /vendor stuff
    ["/opt/vendor/conf/vendor.conf"],
]


def manage(source, target):
    """Do the linking."""
    if os.path.islink(target) or os.path.isfile(target):
        os.unlink(target)
    if not os.path.isfile(source):
        print(f"Skip symlink for {source}, file does not exist")
        return
    os.symlink(source, target)


def symlinks():
    """Manage the symlinks we set above."""
    for arg in SYMLINKS:
        source = arg[0]
        fn = os.path.basename(source) if len(arg) == 1 else arg[1]
        target = f"{APACHECONF}/{fn}"
        manage(source, target)


def copy_verbatim():
    """Take everything in apache_conf.d verbatim."""
    for fn in os.listdir(f"{THISREPO}/apache_conf.d"):
        source = f"{THISREPO}/apache_conf.d/{fn}"
        target = f"{APACHECONF}/{fn}"
        manage(source, target)


def compute_environ():
    """Figure out things about our current host."""
    env = {}
    # get hostname
    env["hostname"] = socket.gethostname()
    # Get system memory in GB
    env["memGB"] = (
        os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3)
    )
    env["ThreadsPerChild"] = 64  # No need to modify?
    env["MinSpareThreads"] = env["ThreadsPerChild"] * 2  # conservative
    env["ServerLimit"] = 96
    env["iemwsgi_tc"] = 1  # Not really used on non-iemws
    env["iemwsgi_ap"] = 2  # More likely to be used.
    if env["hostname"].startswith("iemvs"):
        env["iemwsgi_tc"] = 12
        env["iemwsgi_ap"] = 16
        env["MinSpareThreads"] = env["ThreadsPerChild"] * 32
        if env["memGB"] > 40:  # Fatter nodes
            env["ServerLimit"] = 128
    elif env["hostname"].startswith("iem12"):
        env["iemwsgi_ap"] = 16
    elif env["hostname"].startswith("iem16"):
        env["iemwsgi_ap"] = 16
    env["MaxRequestWorkers"] = env["ServerLimit"] * env["ThreadsPerChild"]

    env["wsgi_tc_pp"] = ""
    env["wsgi_ap_pp"] = ""
    # is this a dev machine?
    if os.path.isfile("/etc/IEMDEV"):
        env["wsgi_tc_pp"] = "python-path=/home/akrherz/projects/tilecache/src"
        env["wsgi_ap_pp"] = "python-path=/home/akrherz/projects/pyIEM/src"

    return env


def process_templates(environ):
    """For each template, we load and then replace."""
    for fn in os.listdir(f"{THISREPO}/apache_templates.d"):
        source = os.path.join(THISREPO, "apache_templates.d", fn)
        with open(source, "r", encoding="utf-8") as fh:
            content = fh.read()
        # Do replacements
        content = content.format(**environ)
        # Write to final spot
        target = os.path.join(APACHECONF, fn)
        # could be busted symlinks lying around
        if os.path.islink(target) or os.path.isfile(target):
            os.unlink(target)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)


def main():
    """Go Main Go."""
    environ = compute_environ()
    copy_verbatim()
    process_templates(environ)
    symlinks()


if __name__ == "__main__":
    main()
