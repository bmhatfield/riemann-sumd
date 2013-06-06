Riemann-sumd
===
Python agent for scheduling event generating processes and sending the results to Riemann

What?
---
Riemann-sumd is an agent for scheduling 'tasks', such as commands that conform to the Nagios plugin interface, and sending the results to Riemann. There are multiple task interfaces, such as the Nagios plugin interface, a JSON interface over `stdout`, and a JSON interface from arbitrary URLs.

Why?
---
While configuring my Riemann install, I noticed that the already-built clients were single-purpose daemons that sent their own events to Riemann. To operationalize such a thing, I'd have to deploy and monitor and maintain a fleet of little processes, which I was not interested in doing. In addition, I'd have to create additional little monitoring daemons that reproduce this functionality.

Instead, I decided that I'd prefer to have a small daemon that scheduled customizable tasks to run, and transformed their output into Riemann events. Additionally, I realized that there's a wealth of monitoring scripts out there that cohere quite nicely to the concept of a Riemann event: Nagios checks! If one could run a Nagios check, capture the return code, and send it (and the check's output and performance data) to Riemann as an event, that could be quite useful!

Configuration
---
It's a simple daemon with the capability to perform a few different 'types' of tasks on a schedule.

- `nagios`: Nagios style tasks (IE; return 0 for OK, 2 for CRITICAL, etc)
- `json`: JSON style tasks (Execute a command that returns a JSON list of events over stdout)
- `http_json`: JSON retrieved over HTTP (See below for schema)  
- Deprecated: `cloudkick`: Has been renamed to `http_json`

The configuration aims to be dead simple: in a /etc/riemann/tasks.d/ directory, create SOMETASK.task with the following YAML-style fields:

```
# Required
service: "Random State"
arg: 'bash -c "exit $((RANDOM % 4))"'
type: "nagios"

# If omitted, defaults to 60s
ttl: 60

# If omitted, defaults to empty set
tags: ['flapper', 'notify']


# If omitted, defaults to system's hostname
host: "myhost.example.com"

# Set arbitrary attributes, optional
attributes:
	window-size: 3
	contact-email: "ops_team@yourcompany.com"

# Assign a specific 'performance data' key to be the 'metric' for the event.
# Must be prepended with "task_", all others will be added as attributes on the event.
# If omitted, the first performance data pair returned by the check is used
metric: task_load5

# Set a grace period on the events sent to Riemann before the expired.
# If omitted, defaults to 5.
ttl_multiplier: 5

# Set a note to be prepended to the description attached to the event. Defaults to ""
note: "SOMERANDOMSTRING" (also settable per-item in cloudkick.json)
```

Internal Notes
---
Internally, the scheduler calculates the task's skew, and schedules the next event of this task to run at now + offset - skew. When that deadline is near, the scheduler returns the task, which is started in a subprocess and added to a queue to be examined later. A pool of worker threads pull the next already-running task off the queue, join it, wait for it to complete, and send the results to Riemann.

Dependencies
---
> **YAML parser**  
> http://pyyaml.org/wiki/PyYAML  
> Ubuntu: python-yaml  
> `import yaml ` 

> **Daemonizing library** - implements unix daemon functionality nicely  
> http://pypi.python.org/pypi/python-daemon/  
> Ubuntu: python-daemon  
> `import daemon ` 

> **Riemann client library**, depends on 'protobuf'  
> https://github.com/banjiewen/bernhard  
> Ubuntu: python-protobuf  
> Ubuntu: -does not exist-  
> `import bernhard`

> **Requests**  
> http://docs.python-requests.org/en/latest/  
> Ubuntu: python-requests  
> `import requests`  


Nagios Plugin Interface
---
For documentation about the Nagios Plugin Interface, see the [Plugin Interface Documentation](http://nagiosplug.sourceforge.net/developer-guidelines.html#PLUGOUTPUT) and the [Performance Data Format](http://nagiosplug.sourceforge.net/developer-guidelines.html#AEN201)


HTTP JSON Interface
---
The JSON structure should contain an entry for each event, as well as metrics and other data:
```
{
   "status":"All systems go",
    "state":"ok",
    "enabled":true,
    "metrics":[
        {
            "name":"Some Queue Count",
            "state":"ok",
            "value":0,
            "warn_threshold":4500,
            "error_threshold":9000
        },
        {
            "name":"Other Queue Count",
            "state":"ok",
            "value":38,
            "warn_threshold":4500,
            "error_threshold":9000
        }
    ]
}
```
