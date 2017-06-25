JIRA Metrics Data extract utility
=================================

This utility helps extract data from JIRA for processing with the
ActionableAgile™ Analytics tool (https://www.actionableagile.com/analytics-tools/),
as well as ad-hoc analysis using Excel.

This version of the tool is a fork from Martin (https://github.com/optilude/jira-cycle-extract). It has been modified to produce metrics based on issue sizes in adition to the existing metrics based on issue counts. Additional exports of issue data size changes enable easier backlog change analysis.

It will produce a CSV file with one row for each JIRA issue matching a set of
filter criteria, containing basic information about the issue as well as the
date the issue entered each step in the main cycle workflow.

This data can be used to produce a Cumulative Flow Diagram, a cycle time
scatterplot, a cycle time histogram, and other analytics based on cycle time.

To make it easier to draw these diagrams, the tool can also be used to output
CSV files with pre-calculated values for charting in e.g. Excel.

Finally, if you have the right dependencies installed, it can output basic
charts as images.

Installation
------------

Install Python 2.7 or Python 3.5 and pip. See http://pip.readthedocs.org/en/stable/installing/.

Install using `pip`::

    $ pip install jira-metrics-extract

To install cli and all dependencies down load the requirements.txt file and then install using `pip`::

    $ pip install -r requirements.txt

This will install a binary called `jira-metrics-extract`. You can test that it was
correctly installed using::

    $ jira-metrics-extract --help

If you are using Anaconda then download environment.yml.

Install using `conda`::

    $ conda env create -f environment.yml

Activate the new environment:

Linux, OS X: source activate jira-metrics
Windows: activate jira-metrics

You can test that it was correctly installed using::

    $ jira-metrics-extract --help

If you only installed the jira-metrics-extract with pip and you want to use the built-in charting capabilities, then you need to install Seaborn
(which in turn installs Matplotlib and SciPy) and Statsmodels. You can get
these with the `charting` extra::

    $ pip install jira-metrics-extract[charting]

These dependencies are not installed by default because they can sometimes
be a bit tricky to install.

Using Docker
------------

If you have Docker installed, you can run `jira-metrics-extract` as a docker image::

    $ docker run --rm -it -v "$PWD":/data optilude/jira-metrics-extract:latest --help

This will map the working directory (`/data`) of the containerised
application to the current working directory (`$PWD`). Any files you
specify on the command line (without any further path prefixes) will be
read from or output to the current directory, e.g::

    $ docker run --rm -it -v "$PWD":/data myhomedir/jira-metrics-extract:latest config.yml cycle.csv

Configuration
-------------

Write a YAML configuration file like so, calling it e.g. `config.yaml`::

        # How to connect to JIRA?
        Connection:
            domain: https://myserver.atlassian.net/
            username: myusername # If missing or and not in an environment var, you will be prompted at runtime
            password: secret     # If missing or and not in an environment var, you will be prompted at runtime
            verify: False # If missing True is assumed.

        #Criteria:
        #    Project:
        #        - ATCM # JIRA project key. Can query across multiple projects, add additional rows.
        #    Issue types: # Which issue types to include? - Delivery Story - Task - Bug
        #        - Delivery Story
        #        - Bug
        #    Valid resolutions: # Which resolution statuses to include (unresolved is always included)
        #        - SIGNED OFF
        #        - DONE
        #    JQL:  fixVersion = "ATCM Release 1.0" and priority = Must  AND status != Withdrawn
        #    # Additional filter as raw JQL, optional  eg labels != "Spike"

        #Criteria:
        #     Project:
        #        - ATCM # JIRA project key. Can query across multiple projects, add additional rows.
        #     Issue types:
        #        - Delivery Story
        #        - NFR
        #     Valid resolutions:
        #        - SIGNED OFF
        #        - DONE
        #     JQL: fixVersion = "ATCM Release 1.0" 

        # Compound query when work done by multiple teams as part of a larger programme.
        Queries:
            Attribute: ATCM
            Criteria:
                - Value: Team ATCM
                  Project:
                      - ATCM # JIRA project key. Can query across multiple projects, add additional rows.
                  Issue types: # Which issue types to include? - Delivery Story - Task - Bug
                      - Delivery Story
                      - Bug
                  Valid resolutions: # Which resolution statuses to include (unresolved is always included)
                      - SIGNED OFF
                      - DONE
                  JQL:  fixVersion = "ATCM Release 1.0" and priority = Must  AND status != Withdrawn

                - Value: Team NFR
                  Project:
                      - ATCM # JIRA project key. Can query across multiple projects, add additional rows.
                  Issue types: # Which issue types to include? - Delivery Story - Task - Bug
                      - NFR
                  Valid resolutions: # Which resolution statuses to include (unresolved is always included)
                      - SIGNED OFF
                      - DONE
                  JQL: fixVersion = "ATCM Release 1.0" and priority = Must AND status != Withdrawn

        # Describe the workflow. Each step can be mapped to either a single JIRA
        # status, or a list of statuses that will be treated as equivalent
        # At least two steps are required. Specify the steps in order.

        Workflow:
            Open:
              - OPEN
              - To Do
              - New
              - Not Started
              - Parked
            Analysis:
              - REFINE
              - CANDIDATE FOR SPRINT
              - REFINE
              - Research
            Committed:
              - READY FOR SPRINT
              - Prioritised
            Develop:
              - Reopened
              - BUILD
              - DEVELOPMENT COMPLETE
              - READY FOR BPO SIGN OFF
              - BLOCKED
              - Awaiting review
              - In Progress
              - In review
              - Ready to Test
              - Awaiting Sign Off
              - In QA
              - Integrated
              - Reviewed
              - In Acceptance
              - Story Development
              - Doing
            Done:
              - BUILD TO RELEASE
              - HASS QA
              - READY FOR LIVE
              - DONE
              - Closed
              - Resolved
              - Signed Off

        # High level Actionable Agile Metrics approach to viewing work flow
        # Map key columns to open, backlog, committed, final, complete, abandoned
        Workflow StatusTypes Mapping:
            Open: open
            Analysis : backlog
            Committed : committed
            Develop : final
            Done : complete

        # Map field names to additional attributes to extract
        Attributes:
            #Components: Component/s
            #Priority: Priority
            Release: Fix version/s
            StoryPoints: Story Points
            Labels: labels

        #Known values:
        #    Release:
        #        - "ABC Release 1.0"

        # Additional parameters that can be overridden by command line options
        Max Results: 1000
        Quantiles:
            - 0.5
            - 0.85
            - 0.95
        # This could be date (e.g. 8th Aug 2016) or relative date as in example below
        Charts From: 1 month ago
        Charts To: today 

If you are unfamiliar with YAML, remember that:

* Comments start with `#`
* Sections are defined with a name followed by a colon, and then an indented
  block underneath. `Connection`, `Criteria`, `Workflow` and `Attributes` area
  all sections in the example above.
* Indentation has to use spaces, not tabs!
* Single values can be set using `Key: value` pairs. For example,
  `Project: ABC` above sets the key `Project` to the value `ABC`.
* Lists of values can be set by indenting a new block and placing a `-` in front
  of each list value. In the example above, the `Issue types` list contains
  the values `Story` and `Defect`.

The sections for `Connection`, `Criteria` and `Workflow` are required.

Under `Conection`, only `Domain` is required. If not specified, the script will
look for environment variables and if those are not found it will prompt for 
both or either of username and password when run.

Under `Criteria`, all fields are technically optional, but you should specify
at least some of them to avoid an unbounded query. `Issue types` and
`Valid resolutions` can be set to either single values or lists.

Under `Workflow`, at least two steps are required. Specify the steps in order.
You may either specify a single workflow value or a list (as shown for `Done`
above), in which case multiple JIRA statuses will be collapsed into a single
state for analytics purposes.

The file, and values for things like workflow statuses and attributes, are case
insensitive.

When specifying attributes, use the *name* of the field (as rendered on screen
in JIRA), not its id (as you might do in JQL), so e.g. use `Component/s` not
`components`.

The attributes `Type` (issue type), `Status` and `Resolution` are always
included.

When specifying fields like `Component/s` or `Fix version/s` that may have
lists of values, only the first value set will be used.

Multiple queries
----------------

If it is difficult to construct a single set of criteria that returns all
required issues, multiple `Criteria` sections can be wrapped into a `Queries`
block, like so::

    Queries:
        Attribute: Team
        Criteria:
            - Value: Team 1
              Project: ABC
              Issue types:
                  - Story
                  - Bug
              Valid resolutions:
                  - Done
                  - Closed
              JQL: Component = "Team 1"

            - Value: Team 2
              Project: ABC
              Issue types:
                  - Story
                  - Bug
              Valid resolutions:
                  - Done
                  - Closed
              JQL: Component = "Team 2"

In this example, the `Component` field in JIRA is being used to signify the team
delivering the work, but may also be used for other things. Two JIRA queries
will be run, corresponding to the two `Criteria` blocks.

In addition, a new column called `Team` will be added to the output, as
specified by the `Attribute` field under `Queries`. For all items returned by
the first query, the value will be `Team 1` as per the `Value` field, and for
all items returned by the second query, it will be `Team 2`.

Multi-valued fields
-------------------

Some fields in JIRA can contain multiple values, e.g. `fixVersion`. By default,
the extractor will use the first value in such a field if one is specified in
the `Attributes` block. However, you may want to extract only specific values.

To do so, add a block like the following::

    Attributes:
        Release: Fix version/s

    Known values:
        Release:
            - "R01"
            - "R02"
            - "R03"

The extractor will pick the first "known value" found for the field. If none of
the known values match, the cell will be empty.

Running
-------

To produce the basic cycle time data, run `jira-metics-extract` passing the name
of the YAML configuration file and the name of the output CSV file::

    $ jira-metrics-extract config.yaml data.csv

This will extract a CSV file called `data.csv` with cycle data based on the
configuration in `config.yaml`, in a format compatible with the
ActionableAgile toolset.

If you prefer Excel files for manual analysis::

    $ jira-metrics-extract --format=xlsx config.yaml data.xlsx

If you prefer JSON::

    $ jira-metrics-extract --format=json config.yaml data.json

The JSON format can be loaded by the Actionable Agile Analytics tool if you
self-host it and the single-page HTML file for the AAA tool and the JSON file
are accessible from the same web server, via a URL parameter::

    http://myserver/analytics.html?url=data.json

You can specify a path or full URL, but due to same-origin request restrictions,
your browser is unlikely to let you load anything not served from the same
domain as the analytics web app itself.

**Note:** When the `--format` is set, it applies to all files written, not
just the main cyle data file (see other options below). It is important to be
consistent with the file extensions. In particular, if you are using the `xlsx`
format you should also make sure all output files use a `.xlsx` extension.

There are lots more options. See::

    $ jira-metrics-extract --help

Use the `-v` option to print more information during the extract process.

Use the `-n` option to limit the number of items fetched from JIRA, based on
the most recently updated issues. This is useful for testing the configuration
without waiting for long downloads::

    $ jira-metrics-extract -v -n 10 config.yaml data.csv

To produce **Cumulative Flow Diagram statistics**, use the `--cfd` option::

    $ jira-metrics-extract --cfd cfd.csv config.yaml data.csv

This will yield a `cfd.csv` file with one row for each date, one column for each
step in the workflow, and a count of the number of issues in that workflow state
on that day. To plot a CFD, chart this data as a (non-stacked) area chart. You
should technically exclude the series in the first column if it represents the
backlog!

To produce **cycle time scatter plot statistics**, use the `--scatterplot` option::

    $ jira-metrics-extract --scatterplot scatterplot.csv config.yaml data.csv

This will yield a `scatterplot.csv` file with one row for each item that was
completed (i.e. it reached the last workflow state), with columns giving the
completion date and the number of days elapsed from the item entering the first
active state (i.e. the second step in the workflow, on the basis that the first
item represents a backlog or intake queue) to the item entering the completed
state. These two columns can be plotted as an X/Y scatter plot. Further columns
contain the dates of entry into each workflow state and the various issue
metadata to allow further filtering.

To be able to easily draw a **histogram** of the cycle time values, use the
`--histogram` option::

    $ jira-metrics-extract --histogram histogram.csv config.yaml data.csv

This will yield a `histogram.csv` file with two columns: bin ranges and the
number of items with cycle times falling within each bin. These can be charted
as a column or bar chart.

To find out the 30th, 50th, 70th, 85th and 95th **percentile cycle time** values,
pass the `--percentiles` option::

    $ jira-metrics-extract --percentiles percentiles.csv config.yaml data.csv

To calculate different percentiles use the `--quantiles` option::

    $ jira-metrics-extract --percentiles percentiles.csv --quantiles=0.3,0.5,0.8 config.yaml data.csv

Note that there should not be spaces between the commas!

To find out the **daily throughput** for the last 60 days, use the
`--throughput` option::

    $ jira-metrics-extract --throughput throughput.csv config.yaml data.csv

To use a different time window, e.g. the last 90 days::

    $ jira-metrics-extract --throughput throughput.csv --throughput-window=90 config.yaml data.csv

The various options can be used in combination, and it is technically OK to
skip the second positional (`data.csv`) parameter (in which case the file will
not be written).

If you have charting dependencies installed (see above), there are various
options available to allow you to draw **charts**, for example::

    $ jira-metrics-extract --charts-scatterplot=scatterplot.png config.yaml data.csv

The available charts are:

* `--charts-scatterplot` to draw a **scatterplot** of cycle times, with percentile lines
* `--charts-histogram` to draw a **histogram** of cycle times, with percentile lines
* `--charts-cfd` to draw a **Cumulative Flow Diagram**
* `--charts-throughput` to draw a daily **throughput bar chart**
* `--charts-burnup` to draw a simple **burn-up** chart (completed item count vs. time)
* `--charts-burnup-forecast` to draw a **burn-up chart with a Monte Carlo simulation**
  showing paths towards a completion target. The completion target will by default
  be the number of items in the backlog, but can be set explicitly with the
  `--charts-burnup-forecast-target` options. The simluation by default uses
  100 trials. The number of trials can be set with the
  `--charts-burnup-forecast-trials` option. You can set a deadline marker with the
  `--charts-burnup-forecast-deadline` option, which should be set to a date. If
  you also set `--charts-burnup-forecast-deadline-confidence` to a fraction (e.g.
  `0.85`) it will be used to find a confidence interval in the simulation to which
  the deadline will be compared.
* `--charts-wip` to draw a **WIP boxplot** showing min, max, median and mean WIP
  by week. By default, this will show the last 5 or 6 weeks' of data (depending
  on the weekday). You can change this with the `--charts-wip-window` parameter,
  set to a number of weeks.
* `--charts-ageing-wip` to draw an **ageing WIP chart**: a scatter plot of current
  cycle time against state in the cycle, i.e. how items are trending towards completion.
* `--charts-net-flow` to show a bar chart of the **weekly net flow**:
  departures - arrivals. By default, this will show the last 5 or 6 weeks' of
  data (depending on the weekday). You can change this with the
  `--charts-net-flow-window` parameter, set to a number of weeks.

Also note: all the `--charts-*` options have a corresponding `--charts-*-title`
option that can be used to set a title for the chart.

Finally, to limit the date range of the data shown in the charts, you can use the
options `--charts-from` and `--charts-to` to specify a starting and/or ending 
date (inclusive). Both are optional.

Troubleshooting
---------------

* If Excel complains about a `SYLK` format error, ignore it. Click OK. See
  https://support.microsoft.com/en-us/kb/215591.
* JIRA error messages may be printed out as HTML in the console. The error is
  in there somewhere, but may be difficult to see. Most likely, this is either
  an authentication failure (incorrect username/password or blocked account),
  or an error in the `Criteria` section resulting in invalid JQL.
* If you aren't getting the issues you expected to see, use the `-v` option to
  see the JQL being sent to JIRA. Paste this into the JIRA issue filter search
  box ("Advanced mode") to see how JIRA evaluates it.
* Old workflow states can still be part of an issue's history after a workflow
  has been modified. Use the `-v` option to find out about workflow states that
  haven't been mapped.
* Excel sometimes picks funny formats for data in CSV files. Just set them to
  whatever makes sense.
* If you are on a Mac and you get an error about Python not being installed as
  a framework, try to create a file `~/.matplotlib/matplotlibrc` with the
  following contents::

    backend : Agg
* To install the charting dependencies on a Mac, you probably need to install a
  `gfortran` compiler for `scipy`. Use Homebrew (http://brew.sh) and install the
  `gcc` brew.

Ad-hoc analysis
---------------

Sometimes, you may want to perform more exploratory, ad-hoc analysis of the
cycle data. `jira-metrics-extract` uses Python Pandas (http://pandas.pydata.org)
to do most of its heavy lifting, and Pandas provides a rich environment for
data science.

The Jupyter Notebook (http://jupyter.org) is a popular way to conduct
interactive, ad-hoc analysis using Pandas (and more!).

If you have this running, here's an example of a notebook that uses
`jira-cycle-extract` to query JIRA with a given YAML file configuration and
makes the data available for further analysis::

    import getpass
    import datetime

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import seaborn as sns

    from jira import JIRA
    from jira_metrics_extract import cycletime, config

    # Print charts in the notebook, using retina graphics
    %matplotlib inline
    %config InlineBackend.figure_format = 'retina'
    sns.set_context("talk")

    # Prompt for JIRA username, password and config file:
    username = raw_input("Username:")
    password = getpass.getpass("Password:")
    config_filename = raw_input("Config file:")

    # Parse options
    options = {}
    with open(config_filename) as config_file:
        options = config.config_to_options(config_file.read())

    # Connect to JIRA
    jira = JIRA(options={'server': options['connection']['domain']}, basic_auth=(username, password))

    # Fetch issues and calculate cycle data as a Pandas DataFrame
    q = cycletime.CycleTimeQueries(jira, **options['settings'])
    cycle_data = q.cycle_data(verbose=False)

    # Calculate other DataFrames for CFD, scatterplot, histogram, percentile and throughput data
    cfd_data = q.cfd(cycle_data)
    scatter_data = q.scatterplot(cycle_data)
    histogram_data = q.histogram(cycle_data)
    quantiles=[.5,.85,.95]
    percentile_data = q.percentiles(cycle_data, percentiles=quantiles)
    daily_throughput_data = q.throughput_data(cycle_data[cycle_data])

You can now do all kinds of analysis on the DataFrames (`cycle_data`, `cfd_data`
and so on).

Changelog
---------
0.38 - 25 June 2017
     * Modify CLI hasattr syntax errors. Replace some with getattr(args,'xxxx',None).

0.37 - 24 June 2017
     * Modify CLI hasattr syntax errors.

0.36 - 24 June 2017
     * Modify CLI hasattr function incorrectly formatted. Fixed in a number of places.

0.35 - 24 June 2017
     * Modify CLI so that some additional argparse parameters used for filenames are cleaned of spaces and newlines with strip().

0.34 - 24 June 2017
     * Modify CLI so that some argparse parameters used for filenames are cleaned of spaces and newlines with strip().

0.33 - 24 June 2017
     * Modify CLI file so that some argparse parameters are tested for with hasattr function.

0.32 - 24 June 2017
     * Modify CLI file so argparse optional commandline options default to None

0.31 - 24 June 2017
     * Modify CLI file so that logic copes with missing  optional commandline options

0.30 - 13 June 2017
     * Server SSL certificate incorrectly configured. Added verify flag as an option in connection section of configuration yaml file. If verify is False 
    
0.28 - 19 May 2017
     * Filename of CFD file not correct. Fixed.

0.28 - 19 May 2017
     * Write out two files with CFD data. One that can be plotted as stacked.

0.27 - 17 May 2017
     * Forgot to update setup.py version number for release. Update and re-publish.

0.26 - 17 May 2017
     * Update to better deal with related issues. Better error handling with links and stop looking up parent Epics as some issue types do not have Epic parents, and Epics use custom fields in each Jira instance.

0.24 - 2 Feb 2017
     * Replace raw_input which is not python 3 compatible with getpass.getuser input.

0.23 - 19 Jan 2017
     * Fix capitalization of domain, username and password in config options so that using environment vars for connection settings work.

0.22 - 19 Jan 2017
     * Fix spelling mistake changed foreacst to forecast in cli.py.

0.21 - 18 Jan 2017
     * Updated setup.py to pin dateparser<=0.5.0 as later version uses a downsteam library ephem that does not work on Windows.

0.20 - 18 Jan 2017
     * Fixed bug that caused an error when the --quantiles commandline was used.

0.19 - 14 Dec 2016
     * When creating cfd and burnup charts, zero sized issues were sized as 1 point. Now counted as zero points to avoid confusion between direct Jira download.
     * Fixed bug where forecast target line was caculated as the maximum rather than the latest value in backlog cumulative history.

0.18 - 04 Dec 2016
     * Commentout line that created zero length issuelinks.csv file in cycletime.py.

0.17 - 29 Nov 2016
     * Don't try to create a forecast chart if no issues have been completed.
     * See specifying warning as suggested by ruamel.yaml module works. 

0.16 - 25 Nov 2016
     * Fixed bug that ignored issues that were created with a storypoint size that has never changed. Impacted CFD and forecaste
     * Export of issue links and parent epics to csv file - Useful for identifying issue dependencies.

0.15 - 22 Nov 2016
     * Changed the creation of temp buffer creation from in memory spooled to buffered disk for MS-Windows users.

0.13 - 31 Oct 2016
     * Deal with differences in dealing with unicode jira issue summaries betwee Python 2 and 3
     * Return pipe delimited values for issue fields such as labels and Components
     * Save day by day file changes to make it easier to see backlog story size change with pivot table analysis

0.12 - 27 Oct 2016
     * Created new package jira-metrics-extract based on https://github.com/optilude/jira-cycle-extract
     * CFD can also be produced based on issue Story Points size
     * Issue size history can be extracted and saved.

0.10 - June 8 2016
    * Added title options for all charts
    * Added deadline option for burnup forecast chart

0.9 - May 31 2016
    * Add Docker documentation

0.8 - May 30 2016
    * Fixed a bug with calculating the CFD when statuses are skipped
    * Added --throughput output
    * Percentiles are now saved to file, not printed, when using --percentiles
    * Adding charting output (with optional dependencies - see above)

0.7 - January 22 2016
    * Add support for `--format=json`
    * Output all dates in ISO format (YYYY-MM-DD)

0.6 - January 20 2016
    * Add support for `Queries` and `Known values`.

0.5 - November 8 2015
    * When an issues moves between two JIRA states that are mapped to the same
      workflow step, record the *earliest* date, not the most recent
    * When an issue moves backwards in the flow as defined by the sequence of
      workflow steps, retain the *earliest* date the issue entered the given
      step (and erase any dates recorded for all subsequent steps)

0.4 - October 31 2015
    * Fix encoding errors when summary contains non-ASCII characters

0.3 - October 11 2015
    * Add proper support for `--cfd`, `--scatterplot`, `--percentiles` and
      `--histogram`
    * Fix some typing issues with the main cycle data extract.

0.2 - October 10 2015
    * Fix documentation errors

0.1 - October 10 2015
    * Initial release
