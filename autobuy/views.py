from django.shortcuts import render, HttpResponse


def base_view(request):
    return render(request, 'autobuy/base.html', {})
