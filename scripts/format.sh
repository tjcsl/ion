#!/bin/bash
autopep8 -ir -aa --experimental .
docformatter -ir --wrap-summaries 100 .
