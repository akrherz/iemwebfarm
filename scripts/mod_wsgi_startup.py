"""Invoked at mod-wsgi startup to get certain libraries loaded!"""

import os
import sys
import traceback
import warnings

# These need set before importing matplotlib
envpath = "/opt/miniconda3/envs/prod"
# Since we are not sourcing the conda env, we need to set some things
os.environ["PROJ_LIB"] = f"{envpath}/share/proj"
# Don't want proj going out to download stuff
os.environ["PROJ_NETWORK"] = "off"
os.environ["MPLCONFIGDIR"] = "/var/cache/matplotlib"
os.environ["CARTOPY_OFFLINE_SHARED"] = f"{envpath}/share/cartopy"

# Add webfarm repos that have their own pylib to the path
for repo in ["iem", "depbackend"]:
    repodir = f"/opt/{repo}/pylib"
    if repodir not in sys.path and os.path.isdir(repodir):
        sys.path.insert(0, repodir)

from pyiem.plot.use_agg import plt  # noqa
from pyiem.util import LOG  # noqa
import pandas as pd  # noqa


# https://stackoverflow.com/questions/22373927/get-traceback-of-warnings
def warn_with_traceback(
    message, category, filename, lineno, file=None, line=None
):
    """Give local debugging a chance."""
    log = file if hasattr(file, "write") else sys.stderr
    traceback.print_stack(file=log)
    log.write(
        warnings.formatwarning(message, category, filename, lineno, line)
    )


# pandas 2.2 warning with fillna
pd.set_option("future.no_silent_downcasting", True)

warnings.showwarning = warn_with_traceback
# Stop pandas UserWarning for now in prod
if os.path.exists("/etc/IEMDEV"):
    # Some debugging
    warnings.simplefilter("always", category=ResourceWarning)
else:
    warnings.filterwarnings("ignore", category=UserWarning)
