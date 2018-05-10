#!/usr/bin/env python3
import os
import sys
import inspect
#print(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from jira_metrics_extract import cli,charting,config,cycletime,query
#import jira_metrics_extract
from tdda.referencetest.referencetestcase import ReferenceTestCase, tag

class MyTest(ReferenceTestCase):
    @tag
    def test_my_csv_file(self):
        cwd = os.getcwd()

        path_to_test_dir = os.path.join(os.path.dirname(os.path.dirname(cli.__file__)), 'tests')
        expected_data = os.path.join(path_to_test_dir, 'expected.csv')
        output_data = os.path.join(cwd,'output.csv')

        # -b =Flag to set username and password to empty strings. Requred to log into public Jira instance.
        my_argv = ['-v', '-b', '-n', '100',
                   '--format', 'csv',
                   '--cfd', 'cfd.csv',
                   '--separator','comma', #tdda verify function only works with comma delimited files
                   'config.yaml', output_data]
        # my_argv = ['-v','-b','-n', '100',
        #            '--format','csv',
        #            '--points','StoryPoints',
        #            '--links','edges.csv',
        #            '--separator', 'comma',  # tdda verify function only works with comma delimited files
        #            '--cfd', 'cfd.csv',
        #            'config.yaml','output.xlsx'] # '--cfd','cfd.csv',
        # my_argv = ['-v', '-n', '200',
        #            '--no-changelog',
        #            '--points=StoryPoints',
        #            '--separator', 'comma',  # tdda verify function only works with comma delimited files
        #            '--links=edges.csv',
        #            'config.yaml', 'output-points.csv']
        # my_argv = ['-v','-n', '100',
        #            '--format','csv',
        #            '--points','StoryPoints',
        #            '--separator', 'comma',  # tdda verify function only works with comma delimited files
        #            '--links','edges.csv',
        #            '--cfd', 'cfd.csv',
        #            'CPP-Issues.yaml','cpp-output.tsv'] # '--cfd','cfd.csv',
        # my_argv = ['-v','-n', '100',
        #            '--format','csv',
        #            '--separator', 'comma',  # tdda verify function only works with comma delimited files
        #            'USERS.yaml','users.tsv'] # '--cfd','cfd.csv',

        cli.main(my_argv) # Run the code

        self.assertCSVFileCorrect(output_data, expected_data)

if __name__ == '__main__':
    ReferenceTestCase.main()
