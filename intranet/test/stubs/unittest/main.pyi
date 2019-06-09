# Stubs for unittest.main (Python 3.5)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any
from .signals import installHandler as installHandler

MAIN_EXAMPLES = ...  # type: Any
MODULE_EXAMPLES = ...  # type: Any

class TestProgram:
    module = ...  # type: Any
    verbosity = ...  # type: Any
    failfast = ...  # type: Any
    catchbreak = ...  # type: Any
    buffer = ...  # type: Any
    progName = ...  # type: Any
    warnings = ...  # type: Any
    exit = ...  # type: Any
    tb_locals = ...  # type: Any
    defaultTest = ...  # type: Any
    testRunner = ...  # type: Any
    testLoader = ...  # type: Any
    def __init__(self, module='', defaultTest=None, argv=None, testRunner=None, testLoader=..., exit=True, verbosity=1, failfast=None, catchbreak=None, buffer=None, warnings=None, *, tb_locals=False): ...
    def usageExit(self, msg=None): ...
    testNames = ...  # type: Any
    def parseArgs(self, argv): ...
    test = ...  # type: Any
    def createTests(self): ...
    result = ...  # type: Any
    def runTests(self): ...

main = ...  # type: Any