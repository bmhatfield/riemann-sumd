#!/usr/bin/env python
from distutils.core import setup
from distutils.file_util import copy_file
import platform

version = "0.1.0"

setup(name="riemann-sumd",
      version=version,
      description="Python agent for scheduling event generating processes and sending the results to Riemann",
      author="Brian Hatfield",
      author_email="bmhatfield@gmail.com",
      url="https://github.com/bmhatfield/riemann-sumd",
      package_dir={'': 'lib'},
      py_modules=['event', 'loader', 'scheduler', 'sender', 'task'],
      data_files=[('/etc/init/', ["init/ubuntu/sumd.conf"]),
                  ('/etc/sumd', ['examples/etc/sumd/sumd.conf']),
                  ('/etc/sumd/tasks.d', ['examples/etc/sumd/tasks.d/simple.task.example']),
                  ('/etc/sumd/tags.d', ['examples/etc/sumd/tags.d/simple.tag.example'])],
      scripts=["bin/sumd"]
    )

copy_file('/lib/init/upstart-job', '/etc/init.d/sumd', link='sym')