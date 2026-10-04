from setuptools import setup

setup(name='auv2027_autonomy', version='0.1.0', packages=['auv2027_autonomy'],
      data_files=[('share/ament_index/resource_index/packages', ['resource/auv2027_autonomy']),
                  ('share/auv2027_autonomy', ['package.xml'])],
      entry_points={'console_scripts': ['platform = auv2027_autonomy.ros:main']})
