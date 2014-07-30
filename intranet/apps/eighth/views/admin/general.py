from django.shortcuts import render
from intranet.apps.auth.decorators import eighth_admin_required


@eighth_admin_required
def eighth_admin_index_view(request):
    return render(request, "eighth/admin/index.html", {})
