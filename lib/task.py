# Subprocess
import subprocess

# For splitting command lines into popen forms
# http://docs.python.org/2/library/subprocess.html#subprocess.Popen
import shlex

class Task():
	def __init__(self, command, ttl, shell=False):
		self.command = shlex.split(command)
		self.ttl = ttl
		self.use_shell = shell

	def run(self):
		self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE)

	def result(self):
		stdout, sterr = self.process.communicate()
		return (stdout, stderr, self.process.returncode)