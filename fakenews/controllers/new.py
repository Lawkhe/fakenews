from rest_framework.decorators import api_view
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect, JsonResponse
from fakenews.models import Type, Origin, News, Media, Content
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords

import pickle
import re

def list(request):
    if 'user' in request.session:
        news_values = News.objects.filter(user_id=request.session['user']['id'], state=True).order_by('-id')
        return render(request, 'new/list.html', 
            context={'session': request.session['user'], 'news': news_values})
    else:
        return HttpResponseRedirect('/login/')

@never_cache
def create(request):
    if 'user' in request.session:
        if request.method == "POST":
            data = request.POST

            if ('type' in data and data['type'] != '' and 
                'origin' in data and data['origin'] != '' and 
                'title' in data and data['title'] != ''):
                
                try:
                    type_val = Type.objects.get(name=data['type'])
                except Type.DoesNotExist:
                    type_val = Type()
                    type_val.name = data['type']
                    type_val.save()

                try:
                    origin_val = Origin.objects.get(name=data['origin'])
                except Origin.DoesNotExist:
                    origin_val = Origin()
                    origin_val.name = data['origin']
                    origin_val.save()

                new_val = News()
                new_val.user_id = request.session['user']['id']
                new_val.title = data['title']
                new_val.type = type_val
                new_val.origin = origin_val
                new_val.status = 0
                new_val.save()

                if 'text' in data and data['text'] != '':
                    try:
                        media_val = Media.objects.get(name='text')
                    except Media.DoesNotExist:
                        media_val = Media()
                        media_val.name = 'text'
                        media_val.save()

                    prediction = predict(data['text'])

                    content_val = Content()
                    content_val.news = new_val
                    content_val.media = media_val
                    content_val.data = data['text']
                    content_val.result = prediction
                    content_val.save()
                    
                new_val.percentage = prediction
                new_val.status = 1
                new_val.save()


                return HttpResponseRedirect('/new/detail/' + str(new_val.id) + '/')

        return render(request, 'new/create.html', context={'session': request.session['user']})
    else:
        return HttpResponseRedirect('/login/')
   
def predict(text):

    model = pickle.load(open('./fakenews/model2.pkl', 'rb'))
    tfidfvect = pickle.load(open('./fakenews/tfidfvect2.pkl', 'rb'))
    ps = PorterStemmer()

    review = re.sub('[^a-zA-Z]', ' ', text)
    review = review.lower()
    review = review.split()
    review = [ps.stem(word) for word in review if not word in stopwords.words('english')]
    review = ' '.join(review)
    review_vect = tfidfvect.transform([review]).toarray()
    prediction = model.predict(review_vect)

    return prediction
    
def detail(request, pk):
    if 'user' in request.session:
        try:
            new_val = News.objects.get(
                id=pk,
                user_id=request.session['user']['id']
            )

            content_values = Content.objects.filter(news=new_val)
            return render(request, 'new/detail.html', 
                context={'session': request.session['user'], 'new': new_val, 'contents': content_values})
        except News.DoesNotExist:
            return HttpResponseRedirect('/new/list/')
    else:
        return HttpResponseRedirect('/login/')
    
@api_view(['POST'])
def public_change(request):
    if request.method == 'POST':
        data = request.POST
        if 'id' in data and 'state' in data:
            id = data['id']
            public = data['state']
            try:
                new_val = News.objects.get(id=id)
                new_val.public = public
                new_val.save()
                return JsonResponse({"message": "OK"})
            except News.DoesNotExist:
                return JsonResponse({"message": "Error con los Datos"})
    return JsonResponse({"message": "Datos Imcompletos"})