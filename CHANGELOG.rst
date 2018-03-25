Changelog
---------
0.50 (2018-03-25)
                 

     * Fix text and spacing in CHANGELOG.rst

     * Update setup.py so that download_url is based on version variable.


0.49 (unreleased)
                 

- Nothing changed yet.


0.48 (unreleased)
                 

- Nothing changed yet.


0.47 (2018-03-24)
     * Split out change log into CHANGELOG.rst from the README.rst file.
     * Split CHANGELOG.rst out from the README.rst file.

     * Added zip_safe=Flase to the setup.py file.

0.45 - 1 Aug 2017
     * Fixed bug in cycletime caused by routine trying to work with size history when specifying via flag that no history is to be retrived from Jira.

0.45 - 30 July 2017
     * Added the start of testing.
     * Use issue Created date in first issue cycle 'Open' if skipped.
     * Added cli parameter to set jira username and password to blank strings. Useful for testing.

0.43 - 2 July 2017
     * Removed debug print statements left over for adding --no-changelog.

0.43 - 1 July 2017
     * Added --no-changelog commandline flag so that Jira expand changelog is removed. Returns issues with no history.
     * Quicker and smalled API response playloads. Is not possible interate over change history.
     * Was having problems getting results when dealing with BIG issues with a lot of history.

0.42 - 28 June 2017
     * Export burnup_forecast dataframe only with column headers and not the numbered index column.

0.41 - 28 June 2017
     * Convert burnup_forecast series into a dataframe with column headings so that can be saved to file with column headers

0.40 - 28 June 2017
     * Update pandas to_csv function calls that did not specify encoding='utf-8'. Problems opening files on Windows 7.

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
