# Original version taken from http://djangosnippets.org/snippets/186/
# Original author: udfalkso
# Modified version taken from http://djangosnippets.org/snippets/605/
# Modified by: Shwagroo Team
# Modified further by Doug Stryke

import cProfile
import os
import pstats
import re
import resource
import tempfile
import time
from collections import defaultdict
from io import StringIO
from typing import Any, Dict  # noqa

from django.conf import settings
from django.db import connections

# FIXME change log base to something appropriate for the particular installation
PROFILE_LOG_BASE = "/var/tmp/django"
# FIXME change if needed
DATABASE_CONNECTION = "default"

time_columns = [
    ("Middleware time", "middleware_time"),
    ("Elapsed time", "total_time"),
    ("User cpu", "utime"),
    ("System cpu", "stime"),
    ("Query time", "query_time"),
    ("Query count", "query_count"),
    ("Max RSS(kb)", "max_rss"),
]
time_labels = [col[0] for col in time_columns]
time_fields = [col[1] for col in time_columns]
time_stats = {}  # type: Dict[float,Dict[str,Any]]
# Django middleware is class-based. The module is imported, the profiling class
# is instantiated, and the instance added to the middleware stack.
# We put this profiling module on both ends of the middleware stack to obtain
# the time spent in middleware. Consequently we have one imported module but
# two instances so most state is maintained at the module level.
_start_time = None
_middleware_start_time = None
_current_stats = None

words_re = re.compile(r"\s+")
group_prefix_re = [re.compile("^.*/django/[^/]+"), re.compile("^(.*)/[^/]+$"), re.compile(".*")]  # extract module path  # catch strange entries
_log_file_path = None
_prof = None
_profile_layer = False


class ProfileMiddleware:
    """Displays timing or profiling for any view.
    http://yoursite.com/yourview/?time or http://yoursite.com/yourview/?prof

    Record the time taken by Django and the project code to generate the web page and by the database to make the
    queries. Accumulate repeated web page visits and display the accumulated
    statistics in the web browser in place of the normal web page. The availability of this middleware is
    controlled by the DEBUG flas in settings.py. To time a page, add '?time' (or '&time'). To clear
    out accumulated timings, add '&reset'.

    Alternatively, profile the python function calls executed to create the web page and
    display the profiling statistics in the web browser. To profile a page,
    add '?prof' (or '&prof') to the url. By default the statistics are sorted by cumulative time. To
    specify an alternative sort, add one or more 'sort' parameters, e.g.,
    '&sort=time&sort=calls'. By default the display is limited to the first 40 function calls. To
    specify an alternative, add a limit parameter, e.g., '&limit=.50'. To write the profile data to
    a permanent file in `PROFILE_LOG_BASE` add '&log'. To strip the directory paths from the profile
    statistics, add '&strip'. (Note that the file and group summaries are also removed by 'strip'.)
    """

    def __init__(self):
        self._last_uri = None

    def process_request(self, request):
        global _middleware_start_time, _start_time, _log_file_path, _prof
        if settings.DEBUG:
            if "time" in request.GET:
                # outer layer of middleware onion
                if _middleware_start_time is None:
                    _middleware_start_time = time.time()
                else:
                    # inner layer of onion
                    if "reset" in request.GET:
                        time_stats.clear()
                    else:
                        self._auto_reset_time(request)

                    _start_time = time.time()
                    self._start_rusage = resource.getrusage(resource.RUSAGE_SELF)

            elif "prof" in request.GET:
                if _prof is None:
                    _prof = cProfile.Profile()
                if "log" in request.GET and _log_file_path is None:
                    _log_file_path = get_log_file_path("middleware.profile", time.gmtime())

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and ("prof" in request.GET):
            return _prof.runcall(callback, request, *callback_args, **callback_kwargs)

        return None

    def process_response(self, request, response):
        # pylint: disable=unsupported-assignment-operation,unsubscriptable-object
        global _current_stats, _middleware_start_time, _log_file_path, _profile_layer, _prof
        if settings.DEBUG:
            if "time" in request.GET:
                if _current_stats is None:
                    # inner layer of onion
                    _current_stats = self._collect_time()
                else:
                    # outer layer of onion
                    _current_stats["middleware_time"] = time.time() - _middleware_start_time - _current_stats["total_time"]
                    self._display_time(request, response)
                    _middleware_start_time = None
                    _current_stats = None

            elif "prof" in request.GET:
                if _profile_layer:
                    self._profile(request, response)
                    _prof = None
                    _log_file_path = None
                    _profile_layer = False
                else:
                    _profile_layer = True
        return response

    # detect when we start timing a different page and auto-reset stats
    # (another option would be to maintain separate stats)
    def _auto_reset_time(self, request):
        uri = self._get_real_uri(request)
        if self._last_uri is None:
            self._last_uri = uri
        elif uri != self._last_uri:
            time_stats.clear()
            self._last_uri = uri

    _reUri = re.compile(r"^(http.+/)[?&]time.*$")

    def _get_real_uri(self, request):
        uri = request.build_absolute_uri()
        m = self._reUri.match(uri)
        if m is not None:
            return m.group(1)

        return None

    def _collect_time(self):
        # record stats from this request
        stats = time_stats.setdefault(_start_time, {})
        stats["total_time"] = time.time() - _start_time
        self._end_rusage = resource.getrusage(resource.RUSAGE_SELF)
        stats["max_rss"] = self._end_rusage.ru_maxrss
        stats["utime"] = self._elapsed_ru("ru_utime")
        stats["stime"] = self._elapsed_ru("ru_stime")
        queries = connections["DATABASE_CONNECTION"].queries
        stats["query_time"] = sum([float(query["time"]) for query in queries])
        stats["query_count"] = len(queries)
        return stats

    def _display_time(self, request, response):
        # display all stats since last reset
        stats_str = "%-4s %-24s %13s %14s %10s %12s %12s %12s %12s\n" % tuple(["Req", "Start time"] + time_labels)
        count = 0
        mins = defaultdict(int)
        sums = defaultdict(int)
        maxs = defaultdict(int)
        values = defaultdict(list)
        for start_time in sorted(time_stats.keys()):
            stats = time_stats[start_time]
            # accumulate times for summary, except for first request
            count += 1
            for field in time_fields:
                mins[field] = min(stats[field], mins.get(field, 99999))
                sums[field] += stats[field]
                maxs[field] = max(stats[field], maxs[field])
                values[field].append(stats[field])
            # display line
            stats_str += "%-4s %-24s %15.3f %14.3f %10.3f %12.3f %12.3f %12d %12d\n" % tuple(
                [count, time.ctime(start_time)] + [stats[field] for field in time_fields]
            )

        # display summary statistics
        stats_str += "\n%-4s %-24s %15.3f %14.3f %10.3f %12.3f %12.3f %12d %12d\n" % tuple(["", "Minimum"] + [mins[field] for field in time_fields])
        stats_str += "%-4s %-24s %15.3f %14.3f %10.3f %12.3f %12.3f %12d %12d\n" % tuple(
            ["", "Mean"] + [sums[field] / count for field in time_fields]
        )
        stats_str += "%-4s %-24s %15.3f %14.3f %10.3f %12.3f %12.3f %12d %12d\n" % tuple(["", "Maximum"] + [maxs[field] for field in time_fields])
        if count > 1:
            stats_str += "%-4s %-24s %15.3f %14.3f %10.3f %12.3f %12.3f %12d %12d\n" % tuple(
                ["", "Standard deviation"] + [stdev(values[field]) for field in time_fields]
            )

        if response and response.content and stats_str:
            response.content = "<pre>%s\n\noptions: &reset (clear all stats)\n\n%s</pre>" % (request.build_absolute_uri(), stats_str)

    def _elapsed_ru(self, name):
        return getattr(self._end_rusage, name) - getattr(self._start_rusage, name)

    def _profile(self, request, response):
        out = StringIO()
        if "log" in request.GET and _log_file_path is not None:
            _prof.dump_stats(_log_file_path)
            stats = pstats.Stats(_log_file_path, stream=out)
        else:
            with tempfile.NamedTemporaryFile(dir="/tmp") as temp_file:
                _prof.dump_stats(temp_file.name)
                stats = pstats.Stats(temp_file.name, stream=out)
        _prof.clear()

        if "strip" in request.GET:
            stats.strip_dirs()
        sorts = request.GET.getlist("sort")
        if sorts:
            stats.sort_stats(*sorts)
        else:
            stats.sort_stats("cumulative")
        limit = request.GET.get("limit")
        if limit is None:
            limit = 40
        else:
            try:
                limit = int(limit)
            except ValueError:
                try:
                    limit = float(limit)
                except ValueError:
                    pass
        stats.print_stats(limit)
        stats_str = out.getvalue()

        if response and response.content and stats_str:
            response.content = """<pre>%s\n\n
            options: &log (write data to file) &strip (remove directories) &limit=LIMIT (lines or fraction)\n
            &sort=KEY (e.g., cumulative (default), time, calls, pcalls, etc.)\n\n%s</pre>""" % (
                request.build_absolute_uri(),
                stats_str,
            )
            if "strip" not in request.GET:
                response.content += self._summary_for_files(stats_str)

    def _get_group(self, file_name):
        for g in group_prefix_re:
            name = g.findall(file_name)
            if name:
                return name[0]

        return None

    def _get_summary(self, results_dict, total):
        items = [(item[1], item[0]) for item in results_dict.items()]
        items.sort(reverse=True)
        items = items[:40]

        res = "      tottime\n"
        for item in items:
            res += "%4.1f%% %7.3f %s\n" % (100 * item[0] / total if total else 0, item[0], item[1])

        return res

    def _summary_for_files(self, stats_str):
        stats_str = stats_str.split("\n")[8:]

        mystats = {}
        mygroups = {}

        ttl = 0

        for s in stats_str:
            fields = words_re.split(s)
            if len(fields) == 7:
                time_amt = float(fields[2])
                ttl += time_amt
                file_name = fields[6].split(":", 1)[0]

                if file_name not in mystats:
                    mystats[file_name] = 0
                mystats[file_name] += time_amt

                group = self._get_group(file_name)
                if group not in mygroups:
                    mygroups[group] = 0
                mygroups[group] += time_amt

        return (
            "<pre>"
            + " ---- By file ----\n\n"
            + self._get_summary(mystats, ttl)
            + "\n"
            + " ---- By group ---\n\n"
            + self._get_summary(mygroups, ttl)
            + "</pre>"
        )


def get_log_file_path(log_file_path, called_time):
    if not os.path.isabs(log_file_path):
        log_file_path = os.path.join(PROFILE_LOG_BASE, log_file_path)

    log_dir_path = os.path.dirname(log_file_path)

    try:
        os.makedirs(log_dir_path)
    except os.error:
        pass

    (base, ext) = os.path.splitext(log_file_path)
    base += "_" + time.strftime("%Y%m%d-%H%M%S", called_time)
    return base + ext


def stdev(x):
    r"""Calculate standard deviation of data x[]:
        std = sqrt(\sum_i (x_i - mean)^2 \over n-1)
        https://wiki.python.org/moin/NumericAndScientificRecipes
    """
    from math import sqrt  # pylint: disable=import-outside-toplevel

    n = len(x)
    mean = sum(x) / float(n)
    std = sqrt(sum((a - mean) ** 2 for a in x) / float(n - 1))
    return std
