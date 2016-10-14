from .query import QueryManager
import pandas as pd
import numpy as np
import os
import datetime
import csv

class StatusTypes:
    open = 'open'
    backlog = 'backlog'
    accepted = 'committed'
    complete = 'complete'
    abandoned = 'abandoned'

class CycleTimeQueries(QueryManager):
    """Analysis for cycle time data, producing cumulative flow diagrams,
    scatter plots and histograms.

    Initialise with a `cycle`, a list of dicts representing the steps in
    a cycle. Each dict describes that step with keys `name`, `type` (one of
    "backlog", "accepted" or "complete" as per the `StatusTypes` enum) and
    `statuses` (a list of equivalent JIRA workflow statuses that map onto
    this step).
    """

    settings = dict(
        cycle=[  # flow steps, types, and mapped JIRA statuses
            {
                "name": 'todo',
                "type": StatusTypes.backlog,
                "statuses": ["Open", "To Do"],
            },
            {
                "name": 'analysis',
                "type": StatusTypes.accepted,
                "statuses": ["Analysis"],
            },
            {
                "name": 'analysis-done',
                "type": StatusTypes.accepted,
                "statuses": ["Analysis Done"],
            },
            {
                "name": 'development',
                "type": StatusTypes.accepted,
                "statuses": ["In Progress"],
            },
            {
                "name": 'done',
                "type": StatusTypes.complete,
                "statuses": ["Done", "Closed"],
            },
        ]
    )

    def __init__(self, jira, **kwargs):
        settings = super(CycleTimeQueries, self).settings.copy()
        settings.update(self.settings.copy())
        settings.update(kwargs)

        settings['sized_statuses'] = [] # All columns/statuses other than "open" could be sized via Story Points
        settings['none_sized_statuses'] = [] # Only columns/statuses that are of type "open"
        for s in settings['cycle']:
            # Make all states "sized"
            #if (s['type'] == StatusTypes.open):
            #    settings['none_sized_statuses'].append(s['name'])
            #else:
            settings['sized_statuses'].append(s['name'])

        settings['cycle_lookup'] = {}
        for idx, cycle_step in enumerate(settings['cycle']):
            for status in cycle_step['statuses']:
                settings['cycle_lookup'][status.lower()] = dict(
                    index=idx,
                    name=cycle_step['name'],
                    type=cycle_step['type'],
                )

        super(CycleTimeQueries, self).__init__(jira, **settings)

    def cycle_data(self, verbose=False):
        """Build a numerically indexed data frame with the following 'fixed'
        columns: `key`, 'url', 'issue_type', `summary`, `status`, and
        `resolution` from JIRA, as well as the value of any fields set in
        the `fields` dict in `settings`. If `known_values` is set (a dict of
        lists, with field names as keys and a list of known values for each
        field as values) and a field in `fields` contains a list of values,
        only the first value in the list of known values will be used.

        If 'query_attribute' is set in `settings`, a column with this name
        will be added, and populated with the `value` key, if any, from each
        criteria block under `queries` in settings.

        In addition, `cycle_time` will be set to the time delta between the
        first `accepted`-type column and the first `complete` column, or None.

        The remaining columns are the names of the items in the configured
        cycle, in order.

        Each cell contains the last date/time stamp when the relevant status
        was set.

        If an item moves backwards through the cycle, subsequent date/time
        stamps in the cycle are erased.
        """

        cycle_names = [s['name'] for s in self.settings['cycle']]
        accepted_steps = set(s['name'] for s in self.settings['cycle'] if s['type'] == StatusTypes.accepted)
        completed_steps = set(s['name'] for s in self.settings['cycle'] if s['type'] == StatusTypes.complete)

        series = {
            'key': {'data': [], 'dtype': str},
            'url': {'data': [], 'dtype': str},
            'issue_type': {'data': [], 'dtype': str},
            'summary': {'data': [], 'dtype': str},
            'status': {'data': [], 'dtype': str},
            'resolution': {'data': [], 'dtype': str},
            'cycle_time': {'data': [], 'dtype': 'timedelta64[ns]'},
            'completed_timestamp': {'data': [], 'dtype': 'datetime64[ns]'}
        }

        for cycle_name in cycle_names:
            series[cycle_name] = {'data': [], 'dtype': 'datetime64[ns]'}

        for name in self.fields.keys():
            series[name] = {'data': [], 'dtype': 'object'}

        if self.settings['query_attribute']:
            series[self.settings['query_attribute']] = {'data': [], 'dtype': str}

        createJiraCache = False
        if self.settings['cache_jira']:
            if not os.path.exists(self.settings['cache_jira']):
                createJiraCache = True


        if (self.settings['cache_jira'] == None ) or createJiraCache:
            for criteria in self.settings['queries']:
                for issue in self.find_issues(criteria, order='updatedDate DESC', verbose=verbose):

                    item = {
                        'key': issue.key,
                        'url': "%s/browse/%s" % (self.jira._options['server'], issue.key,),
                        'issue_type': issue.fields.issuetype.name,
                        'summary': issue.fields.summary.encode('utf-8'),
                        'status': issue.fields.status.name,
                        'resolution': issue.fields.resolution.name if issue.fields.resolution else None,
                        'cycle_time': None,
                        'completed_timestamp': None
                    }

                    for name, field_name in self.fields.items():
                        item[name] = self.resolve_field_value(issue, name, field_name)

                    if self.settings['query_attribute']:
                        item[self.settings['query_attribute']] = criteria.get('value', None)

                    for cycle_name in cycle_names:
                        item[cycle_name] = None

                    # Record date of status changes
                    for snapshot in self.iter_changes(issue, False):
                        snapshot_cycle_step = self.settings['cycle_lookup'].get(snapshot.status.lower(), None)
                        if snapshot_cycle_step is None:
                            if verbose:
                                print(issue.key, "transitioned to unknown JIRA status", snapshot.status)
                            continue

                        snapshot_cycle_step_name = snapshot_cycle_step['name']

                        # Keep the first time we entered a step
                        if item[snapshot_cycle_step_name] is None:
                            item[snapshot_cycle_step_name] = snapshot.date

                        # Wipe any subsequent dates, in case this was a move backwards
                        found_cycle_name = False
                        for cycle_name in cycle_names:
                            if not found_cycle_name and cycle_name == snapshot_cycle_step_name:
                                found_cycle_name = True
                                continue
                            elif found_cycle_name and item[cycle_name] is not None:
                                if verbose:
                                    print(issue.key, "moved backwards to", snapshot_cycle_step_name, "wiping date for subsequent step", cycle_name)
                                item[cycle_name] = None

                    # Wipe timestamps if items have moved backwards; calculate cycle time

                    previous_timestamp = None
                    accepted_timestamp = None
                    completed_timestamp = None

                    for cycle_name in cycle_names:
                        if item[cycle_name] is not None:
                            previous_timestamp = item[cycle_name]

                            if accepted_timestamp is None and previous_timestamp is not None and cycle_name in accepted_steps:
                                accepted_timestamp = previous_timestamp
                            if completed_timestamp is None and previous_timestamp is not None and cycle_name in completed_steps:
                                completed_timestamp = previous_timestamp

                    if accepted_timestamp is not None and completed_timestamp is not None:
                        item['cycle_time'] = completed_timestamp - accepted_timestamp
                        item['completed_timestamp'] = completed_timestamp

                    for k, v in item.items():
                        series[k]['data'].append(v)

            data = {}
            for k, v in series.items():
                data[k] = pd.Series(v['data'], dtype=v['dtype'])

            result= pd.DataFrame(data,
                columns=['key', 'url', 'issue_type', 'summary', 'status', 'resolution'] +
                        sorted(self.fields.keys()) +
                        ([self.settings['query_attribute']] if self.settings['query_attribute'] else []) +
                        ['cycle_time', 'completed_timestamp'] +
                        cycle_names
            )
            if createJiraCache:
                result.to_pickle(self.settings['cache_jira'])
            return result

        elif not createJiraCache: # Because it already exists
            try:
                result = pd.read_pickle(self.settings['cache_jira'])
            except IOError:
                print('Oh dear did not find the jira cache pickeled to :', self.settings['cache_jira'])
            return result



    def cfd(self, cycle_data,pointscolumn= None, stacked = True ):
        """Return the data to build a cumulative flow diagram: a DataFrame,
        indexed by day, with columns containing cumulative counts for each
        of the items in the configured cycle.

        In addition, a column called `cycle_time` contains the approximate
        average cycle time of that day based on the first "accepted" status
        and the first "complete" status.

        If stacked = True then return dataframe suitable for plotting as stacked area chart
        else return for platting as non-staked or line chart.
        """

        # Define helper function
        def cumulativeColumnStates(df,stacked):
            """
            Calculate the column sums, were the incoming matrix columns represents items in workflow states
            States progress from left to right.
            We what to zero out items, other than right most value to avoid counting items in prior states.
            :param df:
            :return: pandas dataframe row with sum of column items
            """

            # Helper functions to return the right most cells in 2D array
            def last_number(lst):
                if all(map(lambda x: x == 0, lst)):
                    return 0
                elif lst[-1] != 0:
                    return len(lst) - 1
                else:
                    return last_number(lst[:-1])

            def fill_others(lst):
                new_lst = [0] * len(lst)
                new_lst[last_number(lst)] = lst[last_number(lst)]
                return new_lst

            df_zeroed = df.fillna(value=0)  # ,inplace = True   Get rid of non numeric items. Make a ?deep? copy
            if stacked:
                df_result = df_zeroed.apply(lambda x: fill_others(x.values.tolist()), axis=1)
            else:
                df_result = df_zeroed

            sum_row = df_result[df.columns].sum()  # Sum Columns
            return pd.DataFrame(data=sum_row).T  # Transpose into row dataframe and return

        # Define helper function
        def hide_greater_than_date(cell, adate):
            """ Helper function to compare date values in cells
            """
            result = False
            try:
                celldatetime = datetime.date(cell.year, cell.month, cell.day)
            except:
                return True
            if celldatetime > adate:
                return True
            return False  # We have a date value in cell and it is less than or equal to input date

        #print(pointscolumn)

        # List of all state change columns that may have date value in them
        cycle_names = [s['name'] for s in self.settings['cycle']]

        # Create list of columns that we want to return in our results dataFrame
        slice_columns = list(self.settings['none_sized_statuses']) # Make a COPY of the list so that we dont modify the reference.
        if pointscolumn:
            for size_state in self.settings['sized_statuses']:  # states_to_size:
                sizedStateName = size_state + 'Sized'
                slice_columns.append(sizedStateName)
            # Check that it works if we use all columns as sized.
            slice_columns = []
            for size_state in cycle_names:
                sizedStateName = size_state + 'Sized'
                slice_columns.append(sizedStateName)
        else:
            slice_columns = cycle_names


        # Build a dataframe of just the "date" columns
        df = cycle_data[cycle_names].copy()

        # Strip out times from all dates
        df = pd.DataFrame(
            np.array(df.values, dtype='<M8[ns]').astype('<M8[D]').astype('<M8[ns]'),
            columns=df.columns,
            index=df.index
        )

        # Get a list of dates that a issue changed state
        state_changes_on_dates_set = set()
        for state in cycle_names:
            state_changes_on_dates_set = state_changes_on_dates_set.union(set(df[state]))
            # How many unique days did a issue stage state
        # Remove non timestamp vlaues and sort the list
        state_changes_on_dates = filter(lambda x: type(x.date()) == datetime.date,
                                        sorted(list(state_changes_on_dates_set)))



        # Replace missing NaT values (happens if a status is skipped) with the subsequent timestamp
        df = df.fillna(method='bfill', axis=1)


        if pointscolumn:
            storypoints = cycle_data[pointscolumn]
            ids = cycle_data['key']


        # create blank results dataframe
        df_results = pd.DataFrame()
        # For each date on which we had a issue state change we want to count and sum the totals for each of the given states
        # 'Open','Analysis','Backlog','In Process','Done','Withdrawn'
        timenowstr = datetime.datetime.now().strftime('-run-%H-%M-%S')
        for statechangedate in state_changes_on_dates:
            if type(statechangedate.date()) == datetime.date:
                # filterdate.year,filterdate.month,filterdate.day
                filterdate = datetime.date(statechangedate.year, statechangedate.month,
                                           statechangedate.day)  # statechangedate.datetime()

                # Apply function to each cell and only make it visible if issue was in state on or after the filter date
                df_filtered = df.applymap(lambda x: 0 if hide_greater_than_date(x, filterdate) else 1)

                if pointscolumn:
                    df_countable = pd.concat([ids, storypoints, df_filtered], axis=1)
                else:
                    df_countable = df_filtered

                # Because we size issues with Story Points we need to add some additional columns
                # for each state based on size not just count
                if pointscolumn:
                    for size_state in self.settings['sized_statuses']: #states_to_size:
                        sizedStateName = size_state + 'Sized'
                        df_countable[sizedStateName] = df_countable.apply(
                            lambda row: (row[pointscolumn] * row[size_state] if row[pointscolumn] > 0 else (1.0 * row[size_state])), axis=1)

                # Slice out the columns we want for CFD
                # df_slice= df_countable.loc[:,('Open','Analysis','PrioritizedSized','In ProcessSized','DoneSized')]
                #print(slice_columns)
                #df_slice = df_countable.loc[:, ('Open', 'AnalysisSized', 'CommittedSized', 'DevelopSized', 'DoneSized')]

                # For debugging write dataframe to sheet for current day.
                #file_name="countable-cfd-for-day-"+ filterdate.isoformat()+timenowstr+".csv"
                #df_countable.to_csv(file_name, sep='\t', lineterminator='\n', encoding='utf-8', quoting=csv.QUOTE_ALL)

                df_slice = df_countable.loc[:,slice_columns]
                df_sub_sum = cumulativeColumnStates(df_slice,stacked)
                final_table = df_sub_sum.rename(index={0: filterdate})

                # append to results
                df_results = df_results.append(final_table)
        df_results.sort_index(inplace=True)

        df= df_results
        # Count number of times each date occurs, preserving column order
        #df = pd.concat({col: df[col].value_counts() for col in df}, axis=1)[cycle_names]

        # Fill missing dates with 0 and run a cumulative sum
        #df = df.fillna(0).cumsum(axis=0)

        # Reindex to make sure we have all dates
        start, end = df.index.min(), df.index.max()
        df = df.reindex(pd.date_range(start, end, freq='D'), method='ffill')

        return df


    def histogram(self, cycle_data, bins=10):
        """Return histogram data for the cycle times in `cycle_data`. Returns
        a dictionary with keys `bin_values` and `bin_edges` of numpy arrays
        """
        values, edges = np.histogram(cycle_data['cycle_time'].astype('timedelta64[D]').dropna(), bins=bins)

        index = []
        for i, v in enumerate(edges):
            if i == 0:
                continue
            index.append("%.01f to %.01f" % (edges[i - 1], edges[i],))

        return pd.Series(values, name="Items", index=index)

    def throughput_data(self, cycle_data, frequency='1D',pointscolumn= None):
        """Return a data frame with columns `completed_timestamp` of the
        given frequency, either
        `count`, where count is the number of items
        'sum', where sum is the sum of value specified by pointscolumn. Expected to be 'StoryPoints'
        completed at that timestamp (e.g. daily).
        """
        if pointscolumn:
            return cycle_data[['completed_timestamp', pointscolumn]] \
                .rename(columns={pointscolumn: 'sum'}) \
                .groupby('completed_timestamp').sum() \
                .resample(frequency).sum() \
                .fillna(0)
        else:
            return cycle_data[['completed_timestamp', 'key']] \
                .rename(columns={'key': 'count'}) \
                .groupby('completed_timestamp').count() \
                .resample(frequency).sum() \
                .fillna(0)

    def scatterplot(self, cycle_data):
        """Return scatterplot data for the cycle times in `cycle_data`. Returns
        a data frame containing only those items in `cycle_data` where values
        are set for `completed_timestamp` and `cycle_time`, and with those two
        columns as the first two, both normalised to whole days, and with
        `completed_timestamp` renamed to `completed_date`.
        """

        columns = list(cycle_data.columns)
        columns.remove('cycle_time')
        columns.remove('completed_timestamp')
        columns = ['completed_timestamp', 'cycle_time'] + columns

        data = (
            cycle_data[columns]
            .dropna(subset=['cycle_time', 'completed_timestamp'])
            .rename(columns={'completed_timestamp': 'completed_date'})
        )

        data['cycle_time'] = data['cycle_time'].astype('timedelta64[D]')
        data['completed_date'] = data['completed_date'].map(pd.Timestamp.date)

        return data

    def percentiles(self, cycle_data, percentiles=(0.3, 0.5, 0.7, 0.85, 0.95,)):
        """Return percentiles for `cycle_time` in cycle data as a DataFrame
        """

        return cycle_data['cycle_time'].dropna().quantile(percentiles)

    @staticmethod
    def burnup_monte_carlo(start_value, target_value, start_date, throughput_data, trials=100):

        frequency = throughput_data.index.freq

        if 'count' in throughput_data.columns:
            data_column_name = 'count'
        else:
            data_column_name = 'sum'

        # degenerate case - no steps, abort
        if throughput_data[data_column_name].sum() <= 0:
            return None

        # guess how far away we are; drawing samples one at a time is slow
        sample_buffer_size = int(2 * (target_value - start_value) / throughput_data[data_column_name].mean())

        sample_buffer = dict(idx=0, buffer=None)

        def get_sample():
            if sample_buffer['buffer'] is None or sample_buffer['idx'] >= len(sample_buffer['buffer'].index):
                sample_buffer['buffer'] = throughput_data[data_column_name].sample(sample_buffer_size, replace=True)
                sample_buffer['idx'] = 0

            sample_buffer['idx'] += 1
            return sample_buffer['buffer'].iloc[sample_buffer['idx'] - 1]

        series = {}
        for t in range(trials):
            current_date = start_date
            current_value = start_value

            dates = [current_date]
            steps = [current_value]

            while current_value < target_value:
                current_date += frequency
                current_value += get_sample()

                dates.append(current_date)
                steps.append(current_value)

            series["Trial %d" % t] = pd.Series(steps, index=dates, name="Trial %d" % t)

        return pd.DataFrame(series)

    def burnup_forecast(self,
        cfd_data,
        throughput_data,
        trials=100,
        target=None,
        backlog_column=None,
        done_column=None,
        percentiles=[0.5, 0.75, 0.85, 0.95],
        sized = ''
    ):
        if len(cfd_data.index) == 0:
            raise Exception("Cannot calculate burnup forecast with no data")
        if len(throughput_data.index) == 0:
            raise Exception("Cannot calculate burnup forecast with no completed items")

        # Debug - what are the column names
        #print("backlog_column --> {}  done_column --> {}".format(backlog_column, done_column))
        #print(cfd_data.info())

        if backlog_column is None:
            backlog_column = cfd_data.columns[0]
        else:
            backlog_column = backlog_column + sized

        if done_column is None:
            done_column = cfd_data.columns[-1]
        else:
            done_column = done_column + sized

        if target is None:
            target = cfd_data[backlog_column].max()

        mc_trials = CycleTimeQueries.burnup_monte_carlo(
            start_value=cfd_data[done_column].max(),
            target_value=target,
            start_date=cfd_data.index.max(),
            throughput_data=throughput_data,
            trials=trials
        )

        if mc_trials is not None:

            for col in mc_trials:
                mc_trials[col][mc_trials[col] > target] = target

            # percentiles at finish line
            finish_dates = mc_trials.apply(pd.Series.last_valid_index)
            finish_date_percentiles = finish_dates.quantile(percentiles).dt.normalize()

        return finish_date_percentiles
