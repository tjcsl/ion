import datetime
import ipaddress

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import make_aware

from ..auth.decorators import reauthentication_required
from ..users.models import User
from .models import Request

DISPLAY_NUM = 500
PAGE_RANGE = 5

HTTP_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "HEAD",
    "OPTIONS",
    "CONNECT",
    "TRACE",
]

TEXT_SEARCH_TYPES = [
    ("equals", "Equals"),
    ("contains", "Contains"),
    ("starts", "Starts with"),
    ("ends", "Ends with"),
]


def logs_context(queryset, request):
    total = queryset.count()
    last = total // DISPLAY_NUM + 1

    try:
        page = int(request.GET.get("page", 1))
        page = min(max(1, page), last)
    except ValueError:
        page = 1

    start = (page - 1) * DISPLAY_NUM
    end = page * DISPLAY_NUM
    rqs = queryset.prefetch_related("user")[start:end]

    context = {
        "rqs": rqs,
        "total": total,
        "start": start + 1 if total > 0 else 0,
        "end": min(end, total),
        "last_page": last,
        "current_page": page,
        "show_first_page": page > PAGE_RANGE + 1,
        "show_first_page_dot": page > PAGE_RANGE + 2,
        "show_last_page": page < last - PAGE_RANGE,
        "show_last_page_dot": page < last - PAGE_RANGE - 1,
    }

    for i in range(1, PAGE_RANGE + 1):
        context[f"next_page_{i}"] = page + i if page + i <= last else None
        context[f"prev_page_{i}"] = page - i if page - i >= 1 else None

    return context


@login_required
@reauthentication_required
def logs_view(request):
    if not request.user.is_global_admin:
        raise Http404

    context = {
        "all_users": User.objects.order_by("username").all(),
        "all_methods": HTTP_METHODS,
        "text_search_types": TEXT_SEARCH_TYPES,
    }

    queries = {}

    if request.GET.get("user", None):
        users = set(request.GET.getlist("user"))
        context["selected_users"] = users.copy()

        if "anonymous" in users:
            users.remove("anonymous")
            queries["user__isnull"] = True

            if len(users) > 0:
                messages.warning(request, "Searching only for anonymous users. Ignoring other users.")

        else:
            users = User.objects.filter(username__in=users)

            if users.count() == 1:
                queries["user"] = users.first()
            elif users.count() > 1:
                queries["user__in"] = users

    if request.GET.get("ip", None):
        ips = set(request.GET.getlist("ip"))
        context["selected_ips"] = ips.copy()
        to_expand = [ip for ip in ips if "/" in ip]

        for ip in to_expand:
            try:
                network = ipaddress.ip_network(ip, strict=False)
                ips.remove(ip)

                if network.num_addresses > 2**16:
                    messages.error(request, f"Subnet too large: {ip}.")
                else:
                    ips |= set(str(ip) for ip in network.hosts())

            except ValueError:
                messages.error(request, f"Invalid IP network: {ip}")

        if len(ips) == 1:
            queries["ip"] = ips.pop()
        else:
            queries["ip__in"] = ips

    if request.GET.get("method", None):
        selected_methods = set(request.GET.getlist("method"))
        context["selected_methods"] = selected_methods.copy()
        if len(selected_methods) == 1:
            queries["method"] = selected_methods.pop()
        else:
            queries["method__in"] = selected_methods

    if request.GET.get("from", None):
        from_time = request.GET["from"]
        context["selected_from"] = from_time
        try:
            from_time = datetime.datetime.strptime(from_time, "%Y-%m-%d %H:%M:%S")
            from_time = make_aware(from_time)
            queries["timestamp__gte"] = from_time
        except ValueError:
            messages.error(request, "Invalid from time.")

    if request.GET.get("to", None):
        to_time = request.GET["to"]
        context["selected_to"] = to_time
        try:
            to_time = datetime.datetime.strptime(to_time, "%Y-%m-%d %H:%M:%S")
            to_time = make_aware(to_time)
            queries["timestamp__lte"] = to_time
        except ValueError:
            messages.error(request, "Invalid to time.")
        context["selected_to"] = request.GET["to"]

    if request.GET.get("path-type", None):
        path_type = request.GET["path-type"]
        context["selected_path_type"] = path_type

        if request.GET.get("path", None):
            path = request.GET["path"]
            context["selected_path"] = path

            if path_type == "contains":
                queries["path__contains"] = path
            elif path_type == "starts":
                queries["path__startswith"] = path
            elif path_type == "ends":
                queries["path__endswith"] = path
            else:
                queries["path"] = path

    if request.GET.get("user-agent-type", None):
        user_agent_type = request.GET["user-agent-type"]
        context["selected_user_agent_type"] = user_agent_type

        if request.GET.get("user-agent", None):
            user_agent = request.GET["user-agent"]
            context["selected_user_agent"] = user_agent

            if user_agent_type == "contains":
                queries["user_agent__contains"] = user_agent
            elif user_agent_type == "starts":
                queries["user_agent__startswith"] = user_agent
            elif user_agent_type == "ends":
                queries["user_agent__endswith"] = user_agent
            else:
                queries["user_agent"] = user_agent

    queryset = Request.objects.filter(**queries)
    context |= logs_context(queryset, request)

    return render(request, "logs/home.html", context)


@login_required
@reauthentication_required
def request_view(request, request_id):
    if not request.user.is_global_admin:
        raise Http404

    rq = get_object_or_404(Request, id=request_id)

    return render(request, "logs/request.html", {"rq": rq})
