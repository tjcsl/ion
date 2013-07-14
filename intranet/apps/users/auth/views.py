# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import AuthenticateForm


def index(request, auth_form=None, user_form=None):
    if request.user.is_authenticated():
        user = request.user
        # print user
        return render(request,
                      'users/info.html',
                      {'user': user})
    else:
        auth_form = auth_form or AuthenticateForm()
        return render(request,
                      'users/auth/login.html',
                      {'auth_form': auth_form, })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticateForm(data=request.POST)

        if form.is_valid():

            login(request, form.get_user())
            return redirect('/')
        else:
            # Failure
            return index(request, auth_form=form)  # Modified to show errors
    return redirect('/')


@login_required
def info(request):
    return render(request, 'users/info.html')


def logout_view(request):
    logout(request)
    return redirect('/')
