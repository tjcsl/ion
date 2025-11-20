#!/bin/bash
cd /usr/local/www/intranet3
PRODUCTION=TRUE DEBUG=FALSE VIRTUAL_ENV='/usr/local/virtualenvs/ion' /usr/local/virtualenvs/ion/bin/python "$@"
