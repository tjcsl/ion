from datetime import datetime


def get_start_date(request):
    return request.session.get("start_date", datetime.now().date())
