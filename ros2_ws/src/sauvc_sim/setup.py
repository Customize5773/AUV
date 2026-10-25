from glob import glob
from setuptools import setup

setup(
    name='sauvc_sim',
    version='0.1.0',
    packages=['sauvc_sim'],
    package_data={'sauvc_sim': ['*.so']},
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/sauvc_sim']),
        ('share/sauvc_sim', ['package.xml']),
        ('share/sauvc_sim/launch', glob('launch/*.launch.py')),
        ('share/sauvc_sim/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    entry_points={'console_scripts': [
        'qualification = sauvc_sim.runtime:mission_main',
        'qualification_referee = sauvc_sim.runtime:referee_main',
        'command_guard = sauvc_sim.runtime:guard_main',
        'perception = sauvc_sim.perception:main',
    ]},
    maintainer='HydroShips team',
    maintainer_email='hydroships@example.invalid',
    description='SAUVC reference arenas for Gazebo Fortress',
    license='Proprietary',
)
