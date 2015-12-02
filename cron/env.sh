#!/bin/bash
cd /usr/local/www/intranet3
DEBUG=FALSE VIRTUAL_ENV='/usr/local/virtualenvs/ion' /usr/local/virtualenvs/ion/bin/python "$@"