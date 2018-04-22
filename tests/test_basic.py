#!/usr/bin/env python3
import os
import sys
#print(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from jira_metrics_extract import cli,charting,config,cycletime,query


if __name__ == '__main__':
    #add you app's options here...
    # -b =Flag to set username and password to empty strings. Requred to log into public Jira instance.
    # my_argv = ['-v','-b','-n', '100',
    #            '--format','csv',
    #            '--cfd', 'cfd.csv',
    #            'config.yaml','output.csv']
    my_argv = ['-v','-b','-n', '100',
               '--format','csv',
               '--points','StoryPoints',
               '--links','edges.csv',
               '--cfd', 'cfd.csv',
               'config.yaml','output.xlsx'] # '--cfd','cfd.csv',
    # my_argv = ['-v', '-n', '200',
    #            '--no-changelog',
    #            '--points=StoryPoints',
    #            '--links=edges.csv',
    #            'config.yaml', 'output-points.csv']
    # my_argv = ['-v','-n', '100',
    #            '--format','csv',
    #            '--points','StoryPoints',
    #            '--links','edges.csv',
    #            '--cfd', 'cfd.csv',
    #            'CPP-Issues.yaml','cpp-output.xlsx'] # '--cfd','cfd.csv',
    sys.exit(cli.main(my_argv))
    #put test conditions here
