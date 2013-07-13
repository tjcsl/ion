# Create your views here.
from django.shortcuts import render
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponse
from .forms import AuthenticateForm


def index(request, auth_form=None, user_form=None):
    # User is logged in
    if request.user.is_authenticated():
        user = request.user

        return render(request,
                      'users/info.html',
                      {})
    else:
        # User is not logged in
        auth_form = auth_form or AuthenticateForm()
        print auth_form.errors
        return render(request,
                      'users/auth/login.html',
                      {'auth_form': auth_form, })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticateForm(data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return HttpResponse("Logged in")
        else:
            # Failure
            return index(request, auth_form=form)  # Modified to show errors
    return redirect('/')


def info(request):
    return render(request, 'users/info.html')


def logout_view(request):
    logout(request)
    redirect('/logout')
