FROM ubuntu:14.04
MAINTAINER Jacob Hoffman-Andrews <jsha@eff.org>

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y python python-pip python-dev
RUN apt-get autoremove && apt-get autoclean
RUN pip install --user numpy pandas scipy matplotlib plotly 
