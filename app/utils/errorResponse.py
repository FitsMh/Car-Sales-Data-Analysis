from django.shortcuts import render


def errorResponse(request, errorMsg):
    return render(request, '404.html', {
        'errorMsg': errorMsg
    })
