from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import HttpResponseRedirect
from fakenews.models import News
from django.db.models import Count, F

def chart(request):
    if 'user' in request.session:
        news_values = News.objects.filter(user_id=request.session['user']['id'], state=True).order_by('-id')
        return render(request, 'dashboard/chart.html', 
            context={'session': request.session['user'], 'news': news_values})
    else:
        return HttpResponseRedirect('/login/')
    
@api_view(['GET'])
def get_data(request, option):
    response = {'status': False}
    """
    Opción:
    1 - Verdad/Falso
    2 - Origen
    """
    try:
        if option == 1:
            news_t = News.objects.filter(user_id=request.session['user']['id'], percentage=1, state=True).count()
            news_f = News.objects.filter(user_id=request.session['user']['id'], percentage=0, state=True).count()
            total = news_t + news_f
            response['data'] = {
                'true': news_t,
                'false': news_f,
                'total': total
            }
        elif option == 2:
            news_origin = News.objects.filter(
                user_id=request.session['user']['id'],
                state=True
            ).select_related(
                'type'
            ).values(
                'type__name',
            ).annotate(
                name=F('type__name'), value=Count('type__id')
            ).order_by('-value').values(
                'name', 'value'
            )
            response['data'] = news_origin
        elif option == 3:
            news_origin = News.objects.filter(
                user_id=request.session['user']['id'],
                state=True
            ).select_related(
                'origin'
            ).values(
                'origin__name',
            ).annotate(
                name=F('origin__name'), value=Count('origin__id')
            ).order_by('-value').values(
                'name', 'value'
            )
            response['data'] = news_origin
        response['status'] = True
    except:
        pass
    return Response(response)