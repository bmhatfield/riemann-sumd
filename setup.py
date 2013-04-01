#!/usr/bin/env python
from distutils.core import setup
import platform

version = "0.1.0"

setup(name="chef-registration",
      version=version,
      description="Python agent for scheduling event generating processes and sending the results to Riemann",
      author="Brian Hatfield",
      author_email="bmhatfield@gmail.com",
      url="https://github.com/bmhatfield/riemann-sumd",
      data_files=[('/etc/init/', ["init/sumd.conf"])],
      scripts=["bin/sumd"]
    )