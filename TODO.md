# TODO list

## Features
- handle SIGTERM and SIGKILL signals to properly kill threads and lemonbar
- add some logging
- define a configuration file for the different threads and output formats
- add colors to the conky elements
- add current windows name in the bar

## Refactoring
- use .format in place of % in strings
- remove output string generation from threads (more MVC approach)
