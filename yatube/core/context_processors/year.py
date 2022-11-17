import datetime as datetime


def year(request):
    return {
        'year': datetime.datetime.now().year
    }
