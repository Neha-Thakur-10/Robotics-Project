import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/neha/gitjazzy/src/install/bme_gazebo_sensors_py'
