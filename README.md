riemann-sumd
============

Python agent for scheduling event generating processes and sending the results to Riemann

Why?
----

While configuring my Riemann install, I noticed that the already-built clients were single-purpose daemons that sent their own events to Riemann. To operationalize such a thing, I'd have to deploy and monitor and maintain a fleet of little processes, which I was not interested in doing.

Instead, I decided that I'd prefer to have a small daemon that scheduled tasks to run, and transformed their output into Riemann events. Additionally, I realized that there's a wealth of monitoring scripts out there that conform quite nicely to the idea of 'state' in a Riemann event: Nagios checks! If one could run a Nagios check, capture the return code, and send it (and the check's output) to Riemann as an event, that could be quite useful!

How?
----

It's a simple daemon with the capability to perform a few different 'types' of tasks on a schedule.

- Nagios style tasks (IE; return 0 for OK, 2 for CRITICAL, etc)
- JSON style tasks (Execute a command that returns a JSON list of events over stdout)
- CloudKick JSON style tasks (much less common, but a specific JSON schema over HTTP)

The configuration aims to be dead simple: in a /etc/riemann/tasks.d/ directory, create SOMETASK.task with the following YAML-style fields:

> service: "state-changer"  
> arg: 'bash -c "exit $((RANDOM % 4))"'  
> ttl: 60  
> tags: ['flapper', 'notify']  
> type: "nagios"  
> host: "myhost.example.com"

( **strong** fields are required)  
**service** - Whatever you'd like to call your service  
**arg** - Some command (including flags) to run  
**ttl** - The frequency that you'd like to run your event  
*tags* - A single item string or a list of tags to apply to this service  
**type** - This maps internally to a class for running the task. Valid values are 'nagios', 'python', 'cloudkick'  
*host* - What host is this event for

Internally, the scheduler calculates the task's skew, and schedules the next event of this task to run at now + offset - skew. When that deadline is near, the scheduler returns the task, which is started in a subprocess and added to a queue to be examined later. A pool of worker threads pull the next already-running task off the queue, join it, wait for it to complete, and send the results to Riemann.

Dependencies
------------

> YAML parser  
> http://pyyaml.org/wiki/PyYAML  
> Ubuntu: python-yaml  
> import yaml  

> Daemonizing library - implements unix daemon functionality nicely  
> http://pypi.python.org/pypi/python-daemon/  
> Ubuntu: python-daemon  
> import daemon  

> Riemann client library, depends on 'protobuf'  
> https://github.com/banjiewen/bernhard  
> Ubuntu: python-protobuf  
> Ubuntu: -does not exist-  
> import bernhard  
