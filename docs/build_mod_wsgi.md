# Building mod-wsgi with conda

conda's provided pkg-config causes `apxs` to fail.  So these steps seem to work.

    - mv /opt/miniconda3/envs/prod/bin/pkg-config /tmp/
    - python -m pip install --upgrade mod-wsgi
    - mv /tmp/pkg-config /opt/miniconda3/envs/prod/bin/pkg-config
