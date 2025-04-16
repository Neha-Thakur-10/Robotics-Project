import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_bme_gazebo_sensors = get_package_share_directory('bme_gazebo_sensors')

    gazebo_models_path = os.path.dirname(pkg_bme_gazebo_sensors)
    os.environ["GZ_SIM_RESOURCE_PATH"] = os.environ.get("GZ_SIM_RESOURCE_PATH", "") + os.pathsep + gazebo_models_path

    # Declare launch arguments
    rviz_launch_arg = DeclareLaunchArgument('rviz', default_value='true', description='Open RViz')
    rviz_config_arg = DeclareLaunchArgument('rviz_config', default_value='rviz.rviz', description='RViz config file')
    world_arg = DeclareLaunchArgument('world', default_value='home.sdf', description='Gazebo world file')
    model_arg = DeclareLaunchArgument('model', default_value='mogi_bot.urdf', description='URDF model file')
    x_arg = DeclareLaunchArgument('x', default_value='2.5', description='Spawn X coordinate')
    y_arg = DeclareLaunchArgument('y', default_value='1.5', description='Spawn Y coordinate')
    yaw_arg = DeclareLaunchArgument('yaw', default_value='-1.5707', description='Spawn Yaw angle')
    sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='True', description='Use simulation time')

    urdf_file_path = PathJoinSubstitution([pkg_bme_gazebo_sensors, "urdf", LaunchConfiguration('model')])

    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bme_gazebo_sensors, 'launch', 'world.launch.py')
        ),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([pkg_bme_gazebo_sensors, 'rviz', LaunchConfiguration('rviz_config')])],
        condition=IfCondition(LaunchConfiguration('rviz')),
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    spawn_urdf_node = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "mogi_bot",
            "-topic", "robot_description",
            "-x", LaunchConfiguration('x'),
            "-y", LaunchConfiguration('y'),
            "-z", "0.5",
            "-Y", LaunchConfiguration('yaw')
        ],
        output="screen",
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    gz_bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock]",
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            "/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model",
            "/camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
            "/imu@sensor_msgs/msg/Imu@gz.msgs.IMU",
            "/navsat@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat",
            "/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan"
        ],
        output="screen",
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    gz_image_bridge_node = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image"],
        output="screen",
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time'), 'camera.image.compressed.jpeg_quality': 75}]
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': Command(['xacro', ' ', urdf_file_path]), 'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')]
    )

    trajectory_node = Node(
        package='mogi_trajectory_server',
        executable='mogi_trajectory_server',
        name='mogi_trajectory_server'
    )

    relay_camera_info_node = Node(
        package='topic_tools',
        executable='relay',
        name='relay_camera_info',
        output='screen',
        arguments=['camera/camera_info', 'camera/image/camera_info'],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(pkg_bme_gazebo_sensors, 'config', 'ekf.yaml'), {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # Create LaunchDescription and add all actions
    launch_description = LaunchDescription([
        rviz_launch_arg, rviz_config_arg, world_arg, model_arg, x_arg, y_arg, yaw_arg, sim_time_arg,
        world_launch, rviz_node, spawn_urdf_node, gz_bridge_node, robot_state_publisher_node,
        trajectory_node, gz_image_bridge_node, relay_camera_info_node, ekf_node
    ])

    return launch_description