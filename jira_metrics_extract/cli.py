from __future__ import print_function
import argparse
import getpass
import json
import datetime
import base64
import sys
import csv
import os
from future.utils import iteritems

import dateutil.parser
from dateparser import parse as relative_parser

import numpy as np
import pandas as pd

from jira import JIRA, JIRAError
JIRAError.log_to_tempfile = False

from .config import config_to_options
from .cycletime import CycleTimeQueries
from . import charting

# dateparser module uses the load stream function in a way that is not save. But as this is an dependent module we will ignore warning at present.
import warnings
from ruamel.yaml.error import UnsafeLoaderWarning
warnings.simplefilter('ignore', UnsafeLoaderWarning)


def eprint(*args, **kwargs):
    """Print to stderr
    """
    print(*args, file=sys.stderr, **kwargs)

def create_argument_parser():
    parser = argparse.ArgumentParser(description='Extract cycle time analytics data from JIRA.')
    parser.add_argument('config', metavar='config.yml', help='Configuration file')
    parser.add_argument('output', metavar='data.csv', nargs='?', help='Output file. Contains all issues described by the configuration file, metadata, and dates of entry to each state in the cycle.')
    parser.add_argument('-v', dest='verbose', action='store_true', help='Verbose output')
    parser.add_argument('-n', metavar='N', dest='max_results', type=int, help='Only fetch N most recently updated issues',default=500)
    parser.add_argument('-b', dest='blankcredentials', action='store_true',help='Flag to set username and password to empty strings.')
    parser.add_argument('--changelog', dest='changelog', action='store_true',help='Get issue history changelog. Default for all queries.')
    parser.add_argument('--no-changelog', dest='changelog', action='store_false',help='DO NOT Get issue history changelog. Limit response size.')
    parser.set_defaults(changelog=True)
    parser.add_argument('--format', metavar='csv|json|xlsx', help="Output format for data (default CSV)")
    parser.add_argument('--points', metavar="StoryPoints", help="By default we use story count, now use given column and use Story Points size for analytics")
    parser.add_argument('--records', metavar='records.json', help="All the ouptut data for issues as JSON records instead of arrays.")
    parser.add_argument('--cfd', metavar='cfd.csv', help='Calculate data to draw a Cumulative Flow Diagram and write to file. Hint: Plot as a (non-stacked) area chart.')
    parser.add_argument('--scatterplot', metavar='scatterplot.csv', help='Calculate data to draw a cycle time scatter plot and write to file. Hint: Plot as a scatter chart.')
    parser.add_argument('--histogram', metavar='histogram.csv', help='Calculate data to draw a cycle time histogram and write to file. Hint: Plot as a column chart.')
    parser.add_argument('--throughput', metavar='throughput.csv', help='Calculate daily throughput data and write to file. Hint: Plot as a column chart.')
    parser.add_argument('--percentiles', metavar='percentiles.csv', help='Calculate cycle time percentiles and write to file.')
    parser.add_argument('--burnup-forecast', metavar='burnup_forecast.csv', help='Calculate forecasted dates percentiles and write to file.')
    parser.add_argument('--size-history', metavar='size_history.csv',
                        help='Get Story Points history and write to file.')
    parser.add_argument('--links', metavar='links_data.tsv', help='Write issue links and epic relationships to file.')

    parser.add_argument('--quantiles', metavar='0.3,0.5,0.75,0.85,0.95', help="Quantiles to use when calculating percentiles")
    parser.add_argument('--backlog-column', metavar='<name>', help="Name of the backlog column. Defaults to the first column.")
    parser.add_argument('--committed-column', metavar='<name>', help="Name of the column from which work is considered committed. Defaults to the second column.")
    parser.add_argument('--final-column', metavar='<name>', help="Name of the final 'work' column. Defaults to the penultimate column.")
    parser.add_argument('--done-column', metavar='<name>', help="Name of the 'done' column. Defaults to the last column.")
    parser.add_argument('--throughput-window', metavar='60', type=int, default=60, help="How many days in the past to use for calculating throughput")
    parser.add_argument('--throughput-window-end', metavar=datetime.date.today().isoformat(), help="By default, the throughput window runs to today's date. Use this option to set an alternative end date for the window.")
    parser.add_argument('--separator', metavar='tab|comma', help="Separator to be used when output format is csv (default tab)")

    if charting.HAVE_CHARTING:

        parser.add_argument('--charts-from', metavar=(datetime.date.today() - datetime.timedelta(days=30)).isoformat(), help="Limit time window when drawing charts to start from this date")
        parser.add_argument('--charts-to', metavar=datetime.date.today().isoformat(), help="Limit time window when drawing charts to end at this date")

        parser.add_argument('--charts-scatterplot', metavar='scatterplot.png', help="Draw cycle time scatter plot")
        parser.add_argument('--charts-scatterplot-title', metavar='"Cycle time scatter plot"', help="Title for cycle time scatter plot")

        parser.add_argument('--charts-histogram', metavar='histogram.png', help="Draw cycle time histogram")
        parser.add_argument('--charts-histogram-title', metavar='"Cycle time histogram"', help="Title for cycle time histogram")

        parser.add_argument('--charts-cfd', metavar='cfd.png', help="Draw Cumulative Flow Diagram")
        parser.add_argument('--charts-cfd-title', metavar='"Cumulative Flow Diagram"', help="Title for CFD")

        parser.add_argument('--charts-throughput', metavar='throughput.png', help="Draw weekly throughput chart with trend line")
        parser.add_argument('--charts-throughput-title', metavar='"Throughput trend"', help="Title for throughput chart")

        parser.add_argument('--charts-burnup', metavar='burnup.png', help="Draw simple burn-up chart")
        parser.add_argument('--charts-burnup-title', metavar='"Burn-up"', help="Title for burn-up charts_scatterplot")

        parser.add_argument('--charts-burnup-forecast', metavar='burnup-forecast.png', help="Draw burn-up chart with Monte Carlo simulation forecast to completion")
        parser.add_argument('--charts-burnup-forecast-title', metavar='"Burn-up forecast"', help="Title for burn-up forecast chart")
        parser.add_argument('--charts-burnup-forecast-target', metavar='<num stories>', type=int, help="Target completion scope for forecast. Defaults to current size of backlog.")
        parser.add_argument('--charts-burnup-forecast-deadline', metavar=datetime.date.today().isoformat(), help="Deadline date for completion of backlog. If set, it will be shown on the chart, and the forecast delta will also be shown.")
        parser.add_argument('--charts-burnup-forecast-deadline-confidence', metavar=.85, type=float, help="Quantile to use when comparing deadline to forecast.")
        parser.add_argument('--charts-burnup-forecast-trials', metavar='100', type=int, default=100, help="Number of iterations in Monte Carlo simulation.")

        parser.add_argument('--charts-wip', metavar='wip', help="Draw weekly WIP box plot")
        parser.add_argument('--charts-wip-title', metavar='"Weekly WIP"', help="Title for WIP chart")
        parser.add_argument('--charts-wip-window', metavar='6', default=6, type=int, help="Number of weeks in the past for which to draw weekly WIP chart")

        parser.add_argument('--charts-ageing-wip', metavar='ageing-wip.png', help="Draw current ageing WIP chart")
        parser.add_argument('--charts-ageing-wip-title', metavar='"Ageing WIP"', help="Title for ageing WIP chart")

        parser.add_argument('--charts-net-flow', metavar='net-flow.png', help="Draw weekly net flow bar chart")
        parser.add_argument('--charts-net-flow-title', metavar='"Net flow"', help="Title for net flow bar chart`")
        parser.add_argument('--charts-net-flow-window', metavar='6', default=6, type=int, help="Number of weeks in the past for which to draw net flow chart")
    return parser

def get_jira_client(connection):
    url = connection['domain']
    token = connection['token']
    try:
        verify = connection['verify']
    except KeyError: #Not found in yaml configuration file
        verify = True # Default should be to verify the certificates to Jira server

    if token:
        username, password = base64.b64decode(token).decode('utf-8').split(':')
    else:
        username = connection['username']
        password = connection['password']

    print("Connecting to ", url)

    if username is None:
        # Fix Python 2.x. raw_input replaced by input in Python 3.x 
        try:
            username = raw_input("Enter Username: ")
        except NameError:
            username = input("Enter username: ")
        except:
            username = getpass.getuser() #Get OS username as as fallback 
            print('No username provided, using username: ' + username)

    if password is None:
        password = getpass.getpass("Enter Password: ")

    if (len(username + password) > 1):
        jiraconnection = JIRA(options={'server': url,'verify': verify}, basic_auth=(username, password))
    else:
        jiraconnection = JIRA(options={'server': url,'verify': verify})
    return jiraconnection

def to_json_string(value):
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    #if isinstance(value, unicode): # Remove as all strings in python 3 are now unicode
    #    return value.encode('utf-8')
    if value in (None, np.NaN, pd.NaT):
        return ""

    try:
        return str(value)
    except TypeError:
        return value

def parse_relative_date(str):
    try:
        return dateutil.parser.parse(str)
    except ValueError:
        return relative_parser(str)

def main(argv=None):
    parser = create_argument_parser()
    # if None passed, uses sys.argv[1:], else use custom args
    args = parser.parse_args(argv)

    if not args.config:
        args.print_usage()
        return

    # Configuration

    with open(args.config) as config:
        options = config_to_options(config.read())

    # Override settings with command line options

    if args.max_results is not None:
        options['settings']['max_results'] = args.max_results

    if getattr(args,'quantiles',None) is not None:
        try:
            quantiles = [float(s.strip()) for s in args.quantiles.split(',')]
            options['settings']['quantiles'] = quantiles
        except (AttributeError, ValueError,):
            print("Invalid value for --quantiles: " + args.quantiles)
            args.print_usage()
            return
    quantiles = options['settings']['quantiles']

    if getattr(args, 'charts_from',None) is not None:
        options['settings']['charts_from'] = args.charts_from
    if getattr(args,'charts_to',None) is not None:
        options['settings']['charts_to'] = args.charts_to

    output_format = args.format.lower() if args.format is not None else 'csv'
    output_separator = '\t' # Default separator is \t
    output_separator = ',' if (args.separator is not None and args.separator.lower() == 'comma') else '\t'

    throughput_window_end = parse_relative_date(args.throughput_window_end) if args.throughput_window_end else datetime.date.today()
    throughput_window_days = args.throughput_window

    if args.blankcredentials:
        options['connection']['username']=''
        options['connection']['password']=''

    # Query JIRA

    try:
        jira = get_jira_client(options['connection'])

        q = CycleTimeQueries(jira, **options['settings'])

        print("Fetching issues (this could take some time)")
        cycle_data = pd.DataFrame()
        size_data = pd.DataFrame()
        edges_data = pd.DataFrame()
        cycle_data, size_data, edges_data  =  q.cycle_data(verbose=args.verbose,result_cycle=cycle_data, result_size=size_data, result_edges=edges_data, changelog=args.changelog)

        if args.points and args.changelog:
            print("Working out size changes of issues over time")
            df_size_history = q.size_history(size_data)
            df_size_history.to_csv(r'size_history.csv', sep=output_separator, encoding='utf-8')  # Save to file.
        else:
            df_size_history = None
    except JIRAError as e:
        eprint(e)
        return 1

    if args.links:
        edges_data.to_csv(args.links, sep=output_separator, index=False,encoding='utf-8')

    #cfd_data = q.cfd(cycle_data)
    print("Working out CFD data")
    cfd_data = q.cfd(cycle_data, size_history = df_size_history, pointscolumn=args.points, stacked=False)
    cfd_data_stackable = q.cfd(cycle_data, size_history = df_size_history, pointscolumn=args.points, stacked=True)

    scatter_data = q.scatterplot(cycle_data)
    histogram_data = q.histogram(cycle_data)
    percentile_data = q.percentiles(cycle_data, percentiles=quantiles)

    #daily_throughput_data = q.throughput_data(
    #    cycle_data[cycle_data['completed_timestamp'] >= (throughput_window_end - datetime.timedelta(days=throughput_window_days))],
    #)

    if args.points:
        daily_throughput_data = q.throughput_data(
            cycle_data[
                cycle_data['completed_timestamp'] >= (
                throughput_window_end - datetime.timedelta(days=throughput_window_days))],
            pointscolumn=args.points)
    else:
        daily_throughput_data = q.throughput_data(
            cycle_data[
                cycle_data['completed_timestamp'] >= (
                    throughput_window_end - datetime.timedelta(days=throughput_window_days))],
        )


    if options['settings']['statusmapping']:
        for key, state in iteritems(options['settings']['statusmapping']): #  # use .items() for python 3  and iteritems() for python 2
            if state == 'complete':
                done_column = key
            if state == 'final':
                final_column = key
            if state == 'committed':
                committed_column = key
            if state == 'backlog':
                backlog_column = key
    else:
        try:

            backlog_column = args.backlog_column or cfd_data.columns[0].replace('Sized', '')
            committed_column = args.committed_column or cfd_data.columns[1].replace('Sized', '')
            final_column = args.final_column or cfd_data.columns[-2].replace('Sized', '')
            done_column = args.done_column or cfd_data.columns[-1].replace('Sized', '')
        except IndexError:
            backlog_column = args.backlog_column
            committed_column = args.committed_column
            final_column = args.final_column
            done_column = args.done_column

    cycle_names = [s['name'] for s in q.settings['cycle']]
    field_names = sorted(options['settings']['fields'].keys())
    query_attribute_names = [q.settings['query_attribute']] if q.settings['query_attribute'] else []

    # Burnup forecast
    if hasattr(args, 'charts_burnup_forecast_target'):
        target = args.charts_burnup_forecast_target
    else:
        target = None
    if hasattr(args, 'charts_burnup_forecast_trials'):
        trials = args.charts_burnup_forecast_trials
    else:
        trials = 1000

    # TODO - parameterise historical throughput
    try:
        if args.points:
            burnup_forecast_data = q.burnup_forecast(
                cfd_data,
                daily_throughput_data,
                trials=trials,
                target=target,
                backlog_column=backlog_column,
                done_column=done_column,
                percentiles=quantiles,
                sized='Sized')
        else:
            burnup_forecast_data = q.burnup_forecast(
                cfd_data,
                daily_throughput_data,
                trials=trials,
                target=target,
                backlog_column=backlog_column,
                done_column=done_column,
                percentiles=quantiles,
                sized='')

    except Exception as e:
        print("Warning: Failed to calculate burnup forecast data")
        burnup_forecast_data = None

    # Write files

    if args.output:
        output_filename = args.output.strip()
        print("Writing cycle data to", output_filename)

        header = ['ID', 'Link', 'Name'] + cycle_names + ['Type', 'Status', 'Resolution','CycleTime'] + field_names + query_attribute_names
        columns = ['key', 'url', 'summary'] + cycle_names + ['issue_type', 'status', 'resolution','cycle_time'] + field_names + query_attribute_names

        if output_format == 'json':
            values = [header] + [map(to_json_string, row) for row in cycle_data[columns].values.tolist()]
            with open(output_filename, 'w') as out:
                out.write(json.dumps(values))
        elif output_format == 'xlsx':
            cycle_data.to_excel(args.output, 'Cycle data', columns=columns, header=header, index=False)
        else:
            cycle_data.to_csv(output_filename, columns=columns, header=header, date_format='%Y-%m-%d', index=False, sep=output_separator, encoding='utf-8')

    if args.records:
        if output_format == 'json':
            output_filename = args.records.strip()
            print("Writing cycle data as JSON records")
            cycle_data.to_json(output_filename, date_format='iso', orient='records')
        else:
            print("Warning: Ignoring cycle data as JSON records. Use --format json")


    if getattr(args,'size_history',None) is not None:
        output_filename = args.size_history.strip()
        print("Writing issue size history data to", output_filename)
        if output_format == 'json':
            size_data.to_json(output_filename, date_format='iso')
        elif output_format == 'xlsx':
            size_data.to_excel(output_filename, 'SIZES')
        else:
            size_data.to_csv(output_filename, columns=['key','fromDate','toDate','size'], sep=output_separator, date_format='%Y-%m-%d', encoding='utf-8')

    if getattr(args,'cfd',None) is not None:
        output_filename = args.cfd.strip()
        print("Writing Cumulative Flow Diagram data to", output_filename)
        if output_format == 'json':
            cfd_data.to_json(output_filename, date_format='iso')
        elif output_format == 'xlsx':
            cfd_data.to_excel(output_filename, 'CFD')
        else:
            cfd_data.to_csv(output_filename, sep=output_separator, encoding='utf-8')

        # Write to disk which is great for debugging and for printing via other external methods
        base_filename=os.path.splitext(os.path.basename(output_filename))[0]
        if cfd_data_stackable.size > 1:
            file_name = "stacked_" + base_filename + '.tsv'
            print("Writing stacked Cumulative Flow Diagram data to ", file_name)
            # quoting = csv.QUOTE_MINIMAL, csv.QUOTE_ALL, csv.QUOTE_NONE, and csv.QUOTE_NONNUMERIC
            cfd_data_stackable.to_csv(file_name, sep=output_separator, encoding='utf-8', quoting=csv.QUOTE_NONE)
        if cfd_data.size > 1:
            file_name = "unstacked_" + base_filename+ '.tsv'
            print("Writing unstacked Cumulative Flow Diagram data to ", file_name)
            # quoting = csv.QUOTE_MINIMAL, csv.QUOTE_ALL, csv.QUOTE_NONE, and csv.QUOTE_NONNUMERIC
            cfd_data.to_csv(file_name, sep=output_separator, encoding='utf-8', quoting=csv.QUOTE_NONE)

    if getattr(args,'scatterplot',None) is not None:
        output_filename = args.scatterplot.strip()
        print("Writing cycle time scatter plot data to", output_filename)
        if output_format == 'json':
            scatter_data.to_json(output_filename, date_format='iso')
        elif output_format == 'xlsx':
            scatter_data.to_excel(output_filename, 'Scatter', index=False)
        else:
            scatter_data.to_csv(output_filename, index=False, sep=output_separator, encoding='utf-8')

    if getattr(args,'percentiles',None) is not None:
        output_filename = args.percentiles.strip()
        print("Writing cycle time percentiles", output_filename)
        if output_format == 'json':
            percentile_data.to_json(output_filename, date_format='iso')
        elif output_format == 'xlsx':
            percentile_data.to_frame(name='percentiles').to_excel(output_filename, 'Percentiles', header=True)
        else:
            percentile_data.to_csv(output_filename, header=True, sep=output_separator, encoding='utf-8')

    if getattr(args,'histogram',None) is not None:
        output_filename = args.histogram.strip()
        print("Writing cycle time histogram data to", args.histogram)
        if output_format == 'json':
            histogram_data.to_json(args.histogram, date_format='iso')
        elif output_format == 'xlsx':
            histogram_data.to_frame(name='histogram').to_excel(args.histogram, 'Histogram', header=True)
        else:
            histogram_data.to_csv(args.histogram, header=True, sep=output_separator, encoding='utf-8')

    if getattr(args,'throughput',None) is not None:
        output_filename = args.throughput.strip()
        print("Writing throughput data to", args.throughput)
        if output_format == 'json':
            daily_throughput_data.to_json(args.throughput, date_format='iso')
        elif output_format == 'xlsx':
            daily_throughput_data.to_excel(args.throughput, 'Throughput', header=True)
        else:
            daily_throughput_data.to_csv(args.throughput, header=True, sep=output_separator, encoding='utf-8')

    if (getattr(args,'burnup_forecast',None) is not None ) and (burnup_forecast_data is not None):
        output_filename = args.burnup_forecast.strip()
        print("Writing burnup forecast data to", output_filename)
        if output_format == 'json':
            burnup_forecast_data.to_json(output_filename, date_format='iso')
        elif output_format == 'xlsx':
            burnup_forecast_data.to_excel(output_filename, 'Forecast', header=True)
        else:
            burnup_forecast_data.to_csv(output_filename, header=True, sep=output_separator, encoding='utf-8', index=False)


    # Output charts (if we have the right things installed)
    if charting.HAVE_CHARTING:

        charts_from = parse_relative_date(options['settings']['charts_from']) if options['settings']['charts_from'] is not None else None
        charts_to = parse_relative_date(options['settings']['charts_to']) if options['settings']['charts_to'] is not None else None

        cycle_data_sliced = cycle_data # Default
        if charts_from is not None:
            cycle_data_sliced = cycle_data[cycle_data['completed_timestamp'] >= charts_from]
        if charts_to is not None:
            cycle_data_sliced = cycle_data[cycle_data['completed_timestamp'] <= charts_to]

        if charts_from is not None and charts_to is None:
            charts_to = pd.datetime.now() # If no upper limit for is provided assume that we can use now as the max value.

        cfd_data_sliced = cfd_data # default, overwrite if date filters exist below if required.
        cfd_data_stackable_sliced = cfd_data_stackable # default, overwrite if date filters exist below if required.
        #cfd_data_sliced = cfd_data[slice(charts_from, charts_to)]
        #cfd_data_stackable_sliced = cfd_data_stackable[slice(charts_from, charts_to)]
        if charts_from and charts_to is not None:
            if args.points:
                # When we use points then the dataframe has a datetime index we need to use to filter rows.
                cfd_data_sliced= cfd_data[(cfd_data.index >= charts_from) & (cfd_data.index <= charts_to)]
                cfd_data_stackable_sliced = cfd_data_stackable[(cfd_data_stackable.index >= charts_from) & (cfd_data_stackable.index <= charts_to)]
            else:
                # When we use count issues(rows) then the dataframe used the first column to rows.
                cfd_data_sliced= cfd_data[(cfd_data.iloc[:, 0] >= charts_from) & (cfd_data.iloc[:, 0] <= charts_to)]
                cfd_data_stackable_sliced = cfd_data_stackable[(cfd_data_stackable.iloc[:, 0] >= charts_from) & (cfd_data_stackable.iloc[:, 0] < charts_to)]


        charting.set_context()

        if args.charts_scatterplot:
            print("Drawing scatterplot in", args.charts_scatterplot)
            charting.set_style('darkgrid')
            try:
                ax = charting.cycle_time_scatterplot(
                    cycle_data_sliced,
                    percentiles=quantiles,
                    title=args.charts_scatterplot_title
                )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_scatterplot, bbox_inches='tight', dpi=300)

        if args.charts_histogram:
            print("Drawing histogram in", args.charts_histogram)
            charting.set_style('darkgrid')
            try:
                ax = charting.cycle_time_histogram(
                    cycle_data_sliced,
                    percentiles=quantiles,
                    title=args.charts_histogram_title
                )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_histogram, bbox_inches='tight', dpi=300)

        if args.charts_cfd:
            print("Drawing CFD in", args.charts_cfd)
            charting.set_style('whitegrid')
            try:
                if args.points:
                    ax = charting.cfd(
                        cfd_data_stackable_sliced,
                        title=args.charts_cfd_title,
                        pointscolumn=args.points
                    )
                else:
                    ax = charting.cfd(
                        cfd_data_sliced,
                        title=args.charts_cfd_title
                    )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_cfd, bbox_inches='tight', dpi=300)

        if args.charts_throughput:
            print("Drawing throughput chart in", args.charts_throughput)
            charting.set_style('darkgrid')
            try:
                ax = charting.throughput_trend_chart(
                    daily_throughput_data,
                    title=args.charts_throughput_title
                )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_throughput, bbox_inches='tight', dpi=300)

        if args.charts_burnup:
            print("Drawing burnup chart in", args.charts_burnup)
            charting.set_style('whitegrid')
            try:
                if args.points:
                    ax = charting.burnup(
                        cfd_data_sliced,
                        backlog_column=backlog_column,
                        done_column=done_column,
                        title=args.charts_burnup_title,
                        sized = 'Sized'
                    )
                else:
                    ax = charting.burnup(
                        cfd_data_sliced,
                        backlog_column=backlog_column,
                        done_column=done_column,
                        title=args.charts_burnup_title,
                        sized=''
                    )

            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_burnup, bbox_inches='tight', dpi=300)

        if args.charts_burnup_forecast:
            target = args.charts_burnup_forecast_target or None
            trials = args.charts_burnup_forecast_trials or 100
            deadline = parse_relative_date(args.charts_burnup_forecast_deadline) if args.charts_burnup_forecast_deadline else None
            deadline_confidence = args.charts_burnup_forecast_deadline_confidence

            print("Drawing burnup forecast chart in", args.charts_burnup_forecast)
            charting.set_style('whitegrid')
            try:
                if args.points:
                    ax = charting.burnup_forecast(
                        cfd_data_sliced,
                        daily_throughput_data,
                        trials=trials,
                        target=target,
                        backlog_column=backlog_column,
                        done_column=done_column,
                        percentiles=quantiles,
                        deadline=deadline,
                        deadline_confidence=deadline_confidence,
                        title=args.charts_burnup_forecast_title,
                        sized='Sized'
                    )
                else:
                    ax = charting.burnup_forecast(
                        cfd_data_sliced,
                        daily_throughput_data,
                        trials=trials,
                        target=target,
                        backlog_column=backlog_column,
                        done_column=done_column,
                        percentiles=quantiles,
                        deadline=deadline,
                        deadline_confidence=deadline_confidence,
                        title=args.charts_burnup_forecast_title,
                        sized=''
                    )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_burnup_forecast, bbox_inches='tight', dpi=300)

        if args.charts_wip:
            print("Drawing WIP chart in", args.charts_wip)
            charting.set_style('darkgrid')
            try:
                ax = charting.wip_chart(
                    q.cfd(cycle_data[cycle_data[backlog_column] >= (datetime.date.today() - datetime.timedelta(weeks=(args.charts_wip_window or 6)))]),
                    start_column=committed_column,
                    end_column=final_column,
                    title=args.charts_wip_title
                )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_wip, bbox_inches='tight', dpi=300)

        if args.charts_ageing_wip:
            print("Drawing ageing WIP chart in", args.charts_ageing_wip)
            charting.set_style('whitegrid')
            try:
                ax = charting.ageing_wip_chart(
                    cycle_data,
                    start_column=committed_column,
                    end_column=final_column,
                    done_column=done_column,
                    title=args.charts_ageing_wip_title
                )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_ageing_wip, bbox_inches='tight', dpi=300)

        if args.charts_net_flow:
            print("Drawing net flow chart in", args.charts_net_flow)
            charting.set_style('darkgrid')
            try:
                ax = charting.net_flow_chart(
                    q.cfd(cycle_data[cycle_data[backlog_column] >= (datetime.date.today() - datetime.timedelta(weeks=(args.charts_net_flow_window or 6)))]),
                    start_column=committed_column,
                    end_column=done_column,
                    title=args.charts_net_flow_title
                )
            except charting.UnchartableData as e:
                print("** WARNING: Did not draw chart:", e)
            else:
                fig = ax.get_figure()
                fig.savefig(args.charts_net_flow, bbox_inches='tight', dpi=300)

    print("Done")
    #sys.exit(0)