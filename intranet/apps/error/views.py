from django.shortcuts import render


def handle_404_view(request):
    return render(request, "error/404.html")


def handle_500_view(request):
    return render(request, "error/500.html")
