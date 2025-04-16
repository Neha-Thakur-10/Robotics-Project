import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/neha/gitjazzy/Week-7-8-ROS2-Navigation/install/bme_ros2_navigation_py'
