from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='jira-metrics-extract',
    version='0.30',
    description='Extract agile metrics data from JIRA',
    long_description=long_description,
    author='Rudiger Wolf',
    author_email='rudiger.wolf@throughputfocus.com',
    url='https://github.com/rnwolf/jira-metrics-extract',
    download_url = 'https://github.com/rnwolf/jira-metrics-extract/tarball/0.30',
    license='MIT',
    keywords='agile metrics jira analytics kanban cfd',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Topic :: Office/Business :: Scheduling"
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[
        'jira',
        'PyYAML',
        'pandas>=0.18',
        'numpy',
        'python-dateutil',
        'dateparser==0.6.0',
        'pydicti',
        'openpyxl',
        'future',
        'pytz'
    ],

    extras_require={
        'charting': ['seaborn', 'matplotlib', 'statsmodels'],
    },

    entry_points={
        'console_scripts': [
            'jira-metrics-extract=jira_metrics_extract.cli:main',
        ],
    },
)
