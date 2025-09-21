# Antares Winjobs
Antares winjobs is a windows based distributed job scheduling system. 
It allows you to schedule and manage antares simulation jobs across multiple Windows machines in a network.

## Modules
The repository contains 3 modules:
- **user:** provides client side functionality to submit and monitor jobs.
- **driver:** driver node managing job distribution and scheduling.
- **worker:** worker node executing pieces of the jobs.

## Supported antares versions
- Antares 8.8: Supported.
- Antares 9.1: Saving pre-generated time series in input folder seems to be broken. Not supported.

## Developer Setup
Repo is built with uv.
Sync using `uv sync` command.

