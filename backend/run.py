# coding: utf-8
from __future__ import absolute_import
from traceback import format_exc
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

def init_db():
    setup_syspath(
        package_root=os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        ),
        current_dir=os.path.dirname(os.path.abspath(__file__)),
    )
    from backend.main.flask_app_mod import app
    from backend.main.models import Task
    from backend.main.factory import db, Base
    with app.app_context():
        db.create_all()
        Base.metadata.create_all(bind=db.engine)
        Task.insert_tasks()


def main(args=None):
    try:
        setup_syspath(
            package_root=os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),
            current_dir=os.path.dirname(os.path.abspath(__file__)),
        )
        from backend.main.flask_app_mod import socket_io, app
        socket_io.run(app, debug=True, host='0.0.0.0')

    except SystemExit:
        raise

    except KeyboardInterrupt:
        return 0

    except BaseException:
        msg = 'Traceback:\n---\n{0}---\n'.format(format_exc())

        sys.stderr.write(msg)

        return 1


if __name__ == '__main__':
    sys.exit(main())
