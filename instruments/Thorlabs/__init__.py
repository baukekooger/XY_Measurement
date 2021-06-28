import os
import platform


# Add library to PYTHONPATH
if platform.architecture()[0] == '64bit':
    os.environ['PATH'] = os.path.dirname(__file__) + os.path.sep + 'lib64' + os.pathsep + os.environ['PATH']
else:
    os.environ['PATH'] = os.path.dirname(__file__) + os.path.sep + 'lib' + os.pathsep + os.environ['PATH']
