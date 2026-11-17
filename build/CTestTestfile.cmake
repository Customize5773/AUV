# CMake generated Testfile for 
# Source directory: /home/rasya/AUV/ros2_ws/src/sauvc_bridge
# Build directory: /home/rasya/AUV/build
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(bridge_lifetime "/home/rasya/AUV/build/bridge_lifetime_test")
set_tests_properties(bridge_lifetime PROPERTIES  ENVIRONMENT "ROS_DOMAIN_ID=231;IGN_PARTITION=sauvc_bridge_lifetime" TIMEOUT "30" _BACKTRACE_TRIPLES "/home/rasya/AUV/ros2_ws/src/sauvc_bridge/CMakeLists.txt;29;add_test;/home/rasya/AUV/ros2_ws/src/sauvc_bridge/CMakeLists.txt;0;")
