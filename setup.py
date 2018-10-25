#!/usr/bin/env python
from distutils.core import setup
import platform

version = "0.7.2"

distro = platform.dist()[0]
distro_major_version = float(platform.dist()[1].split('.')[0])

data_files=[('/etc/sumd', ['examples/etc/sumd/sumd.conf']),
            ('/etc/sumd/tasks.d', ['examples/etc/sumd/tasks.d/simple.task.example']),
            ('/etc/sumd/tags.d', ['examples/etc/sumd/tags.d/simple.tag.example'])]

if distro == 'Ubuntu':
  if distro_major_version >= 16:
    data_files.append(('/usr/lib/systemd/system',
                       ['init/ubuntu/sumd.service']))
  else:
    data_files.append(('/etc/init',
                       ['init/ubuntu/sumd.conf']))

setup(name="riemann-sumd",
      version=version,
      description="Python agent for scheduling event generating processes and sending the results to Riemann",
      author="Brian Hatfield",
      author_email="bmhatfield@gmail.com",
      url="https://github.com/bmhatfield/riemann-sumd",
      package_dir={'': 'lib'},
      py_modules=['event', 'loader', 'scheduler', 'sender', 'task', 'runner'],
      data_files=data_files,
      scripts=["bin/sumd"],
      install_requires=[
            "pyyaml",
            "python-daemon",
            "bernhard>=0.2.2",
            "requests"
        ]
)
