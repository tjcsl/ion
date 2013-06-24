# Create your views here.
from django.shortcuts import render_to_response
def show_landing_page(request):
    """
    docstrings here
    """
    return render_to_response('landing.html', {})
