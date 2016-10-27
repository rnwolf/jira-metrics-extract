FROM python:2-onbuild
MAINTAINER Rudiger Wolf <rudiger.wolf@throughputfocus.com>

WORKDIR /data
VOLUME /data

ENTRYPOINT [ "jira-metrics-extract" ]
