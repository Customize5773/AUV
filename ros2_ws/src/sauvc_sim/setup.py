from glob import glob
from setuptools import setup

setup(
    name='sauvc_sim',
    version='0.1.0',
    packages=['sauvc_sim'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/sauvc_sim']),
        ('share/sauvc_sim', ['package.xml']),
        ('share/sauvc_sim/launch', glob('launch/*.launch.py')),
        ('share/sauvc_sim/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    maintainer='HydroShips team',
    maintainer_email='hydroships@example.invalid',
    description='SAUVC reference arenas for Gazebo Fortress',
    license='Proprietary',
)
