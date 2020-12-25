from __future__ import absolute_import
import os
import sys

def setup_syspath(package_root, current_dir=None):
    removing_dirs = ['', '.']

    if current_dir is not None:
        current_dir = os.path.abspath(current_dir)

        removing_dirs.append(current_dir)

    for path in removing_dirs:
        while True:
            try:
                sys.path.remove(path)
            except ValueError:
                break

    package_root = os.path.abspath(package_root)

    if os.path.isdir(package_root) and package_root not in sys.path:
        sys.path.insert(0, package_root)

    pythonpath = os.environ.get('PYTHONPATH', '')

    pythonpath_dirs = pythonpath.split(os.pathsep)

    pythonpath_dirs = [os.path.abspath(p) for p in pythonpath_dirs]

    if package_root not in pythonpath_dirs:
        pythonpath_dirs.insert(0, package_root)

    new_pythonpath = os.pathsep.join(pythonpath_dirs)

    os.environ['PYTHONPATH'] = new_pythonpath

setup_syspath(
    package_root=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    current_dir=os.path.dirname(os.path.abspath(__file__)),
)

from backend.main import celery
from backend.main.factory import create_app
from backend.main.celery_utils import init_celery

app = create_app()
init_celery(celery, app)