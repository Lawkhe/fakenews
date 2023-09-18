from rest_framework.decorators import api_view
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect, JsonResponse
from fakenews.models import Type, Origin, News, Media, Content
from django.db.models import Q
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from moviepy.editor import VideoFileClip
from threading import Thread
# IA Google
from bardapi import BardCookies

import time
import speech_recognition
import pickle
import re

import cv2
import librosa
import numpy as np
import os

import json
import pywt
import math

# AWS
import boto3
import io

def list(request):
    if 'user' in request.session:
        req_data = request.GET
        page = int(req_data['page']) if 'page' in req_data else 1
        news_values = News.objects.filter(user_id=request.session['user']['id'], state=True).order_by('-id')

        searchnews = ''
        if 'searchnews' in req_data:
            searchnews = req_data['searchnews']
            news_values = news_values.filter(title__icontains=searchnews)

        limit = 10
        x_count = len(news_values)
        x_page = range(1, math.ceil(x_count/10)+1)
        values = (news_values[(page-1)*limit:page*limit])

        # cookie_dict = {
        #     "__Secure-1PSID": "awicyeoWAuOc3f-wK-WWh9I2sEvwI_VYGIDC_UsbCl3d0lyL9oJ-vakbXUbGudRiQq7dgg.",
        #     "__Secure-1PSIDTS": "sidts-CjIBSAxbGazTL1yxV0227KAN0krZEg8F_drp3p8Vb8SN90xjpMVopSW4u5yok15iHeHcFRAA",
        # }

        # bard = BardCookies(cookie_dict=cookie_dict)
        # result = bard.get_answer('Generate a sentence within the context that you consider given the following words, just generate a sentence: Logo, Accessories, Formal Wear, People, Person, Tie, Adult, American Flag, Clothing, Face, Flag, Head, Male, Man, Suit, Angry, Shouting, \n "(help only paragraph text)"')
        # print('result_::::::::::::::::::::')
        # print(result['content'])

        return render(request, 'new/list.html', 
            context={
                'session': request.session['user'],
                'news': values,
                'x_count': x_count,
                'x_page': x_page,
                'page': page,
                'searchnews': searchnews
            })
    else:
        return HttpResponseRedirect('/login/')

@never_cache
def create(request):
    if 'user' in request.session:
        if request.method == "POST":
            data = request.POST
            files = request.FILES

            if ('type' in data and data['type'] != '' and 
                'origin' in data and data['origin'] != '' and 
                'title' in data and data['title'] != '' and (
                ('text' in data and data['text'] != '') or 
                ('audio' in files and files['audio'] != '') or
                ('video' in files and files['video'] != ''))):
                
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

                text_total = ''

                if 'text' in data and data['text'] != '':
                    try:
                        media_val = Media.objects.get(name='text')
                    except Media.DoesNotExist:
                        media_val = Media()
                        media_val.name = 'text'
                        media_val.save()

                    prediction = predict(data['text'])
                    text_total += data['text']

                    content_val = Content()
                    content_val.news = new_val
                    content_val.media = media_val
                    content_val.data = data['text']
                    content_val.result = prediction
                    content_val.save()

                if 'audio' in files and files['audio'] != '':
                    try:
                        media_val = Media.objects.get(name='audio')
                    except Media.DoesNotExist:
                        media_val = Media()
                        media_val.name = 'audio'
                        media_val.save()

                    r = speech_recognition.Recognizer()
                    with speech_recognition.AudioFile(files['audio']) as source:
                        audio_text = r.record(source)

                    try:
                        content_val = Content()
                        content_val.news = new_val
                        content_val.media = media_val
                        content_val.file_path = files['audio']
                        content_val.save()

                        # text = r.recognize_google(audio_text, language='es-ES')
                        text = r.recognize_google(audio_text, language='en-US')
                        prediction = predict(text)
                        
                        content_val.data = " " + text
                        content_val.result = prediction
                        content_val.save()
                        text_total += (" " if text_total else "") + text
                    except speech_recognition.UnknownValueError:
                        content_val.data = "No se pudo transcribir el audio"
                        content_val.save()
                        print('No se pudo transcribir el audio')
                    except speech_recognition.RequestError as e:
                        print('Error al solicitar el servicio de reconocimiento de voz: {0}'.format(e))
                
                process_video = False
                if 'video' in files and files['video'] != '':
                    try:
                        media_val = Media.objects.get(name='video')
                    except Media.DoesNotExist:
                        media_val = Media()
                        media_val.name = 'video'
                        media_val.save()

                    try:
                        content_val = Content()
                        content_val.news = new_val
                        content_val.media = media_val
                        content_val.file_path = files['video']
                        content_val.save()

                        # continue
                        indice_v = verificar_calidad_video('upload/' + str(content_val.file_path))
                        text, indice_a  = verificar_audio_video('upload/' + str(content_val.file_path))
                        
                        prediction_av = predict(text)
                        prediction = 0
                        print('prediction_av::::::::')
                        print(prediction_av)
                        print('indice_v::::::::')
                        print(indice_v)
                        print('indice_a::::::::')
                        print(indice_a)
                        if prediction_av + indice_v + indice_a == 3:
                            prediction = 1
                        
                        data_video = {
                            'indice_v': indice_v,
                            'labels': [],
                            'indice_a': indice_a,
                            'text': text,
                            'paragraph_activities': '',
                        }

                        content_val.data = json.dumps(data_video)
                        content_val.result = prediction
                        content_val.save()

                        # text_total += text
                        process_video = True

                        Thread(target=label_video, args=(new_val, content_val, 'upload/' + str(content_val.file_path), text_total, text)).start()
                        # label_video(content_val, 'upload/' + str(content_val.file_path))
                    except Exception as e:
                        content_val.data = "No se pudo analizar el video"
                        content_val.save()
                        print('Error al solicitar el servicio de analisis de video: {0}'.format(e))

                if not process_video:
                    prediction_total = predict(text_total)
                    new_val.percentage = prediction_total
                    new_val.status = 1
                    new_val.save()

                return HttpResponseRedirect('/new/detail/' + str(new_val.id) + '/')

        return render(request, 'new/create.html', context={'session': request.session['user']})
    else:
        return HttpResponseRedirect('/login/')
   
AWS_ACCESS_KEY_ID = 'AKIAWKYR5AY7ET5LCBAL'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = 'us-east-1'

def label_video(new_val, content_val, video_path, text_total, text_video):
    s3_client = boto3.client('s3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    video_name = 'video_' + str(content_val.id) + '.mp4'
    with open(video_path, 'rb') as video_file:
        response =  s3_client.upload_fileobj(video_file, "custom-labels-console-us-east-1-f477297e29", video_name)

    rekognition_client = boto3.client('rekognition',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    response = rekognition_client.start_label_detection(Video={
        'S3Object': {
            'Bucket': 'custom-labels-console-us-east-1-f477297e29',
            'Name': video_name,
        }
    })
    job_id = response['JobId']
    # Thread(target=label_detection, args=(new_val, content_val, job_id, text_total, text_video)).start()
    label_detection(new_val, content_val, job_id, text_total, text_video)

    

def label_detection(new_val, content_val, job_id, text_total, text_video):
    run_ask_service = True
    
    while run_ask_service:

        rekognition_client = boto3.client('rekognition',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

        response = rekognition_client.get_label_detection(JobId=job_id)
        # IN_PROGRESS | SUCCEEDED | FAILED
        if response['JobStatus'] == 'SUCCEEDED':
            run_ask_service = False
            labels = response['Labels']
            activities = []
            text_activities = ""
            for label in labels:
                if label['Label']['Name'] not in activities:
                    if  label['Label']['Confidence'] > 80:
                        activities.append(label['Label']['Name'])
                        text_activities += label['Label']['Name'] + ", "

            json_data = json.loads(content_val.data)
            json_data['labels'] = activities

            content_val.data = json.dumps(json_data)
            content_val.save()
            
            cookie_dict = {
                "__Secure-1PSID": "awicyeoWAuOc3f-wK-WWh9I2sEvwI_VYGIDC_UsbCl3d0lyL9oJ-vakbXUbGudRiQq7dgg.",
                "__Secure-1PSIDTS": "sidts-CjIBSAxbGazTL1yxV0227KAN0krZEg8F_drp3p8Vb8SN90xjpMVopSW4u5yok15iHeHcFRAA",
            }

            paragraph_activities = ""
            try:
                if text_activities != "":
                    print("Generate a sentence within the context that you consider given the following words: " + text_activities)
                    bard = BardCookies(cookie_dict=cookie_dict)
                    result = bard.get_answer("Generate a sentence within the context that you consider given the following words: " + text_activities + " (text)")
                    print('result_::::::::::::::::::::')
                    print(result)
                    paragraph_activities = result['content']
            except:
                pass

            json_data['paragraph_activities'] = paragraph_activities

            content_val.data = json.dumps(json_data)
            content_val.save()

            text = paragraph_activities + " " + text_video
            text_total += (" " if text_total else "") + text

            prediction_total = predict(text_total)
            new_val.percentage = prediction_total
            new_val.status = 1
            new_val.save()

        elif response['JobStatus'] == 'FAILED': 
            run_ask_service = False
            new_val.percentage = 0
            new_val.status = 1
            new_val.save()

        time.sleep(60)

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
                Q(public=True) | Q(user_id=request.session['user']['id']),
                id=pk,
            )

            content_values = Content.objects.filter(news=new_val)
            content_array = []
            for content in content_values:
                data = content.data
                try:
                    if content.media.name == 'video':
                        print('upload/' + str(content.file_path))
                        # rekognition_video_new('upload/' + str(content.file_path))
                        data = json.loads(content.data)
                except:
                    data = 'Error'
                content_array.append({
                    'media_name': content.media.name,
                    'file_path': str(content.file_path),
                    'data': data
                })
            print(content_array)
            return render(request, 'new/detail.html', 
                context={'session': request.session['user'], 'new': new_val, 'contents': content_array})
        except News.DoesNotExist:
            return HttpResponseRedirect('/new/list/')
    else:
        return HttpResponseRedirect('/login/')

def get_status(request, pk):
    data = request.GET
    
    try:
        new_val = News.objects.get(
            Q(public=True) | Q(user_id=request.session['user']['id']),
            id=pk,
        )
        return JsonResponse({"message": "OK", "status": new_val.status})
    except News.DoesNotExist:
        pass
    return JsonResponse({"message": "Datos Imcompletos"})


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

def public_list(request):
    if 'user' in request.session:
        req_data = request.GET
        
        news_values = News.objects.filter(public=True, state=True).order_by('-id')
        searchnews = ''
        if 'searchnews' in req_data:
            searchnews = req_data['searchnews']
            news_values = news_values.filter(title__icontains=searchnews)

        return render(request, 'new/public.html', 
            context={'session': request.session['user'], 'news': news_values})
    
    else:
        return HttpResponseRedirect('/login/')

from django.conf import settings
from django.views.static import serve

def protected_serve(request, file):
    path_file =  file
    path = '/content/23/'+ path_file
    return serve(request, path, settings.MEDIA_ROOT)

""" Video """
# Función para verificar si el video tiene una calidad baja o sospechosa
def verificar_calidad_video(video_path):
    indice = 1
    
    try:
        cap = cv2.VideoCapture(video_path)

        # count = 0
        # while True:
        #     # Leer el siguiente frame del video
        #     ret, frame = cap.read()

        #     # Verificar si se pudo leer el frame
        #     if not ret:
        #         break

        #     count += 1
        #     # Analizar ruido y compresión en el frame actual
        #     if count == 300:
        #         es_falsa = analizar_ruido_compresion(frame)

        #         if es_falsa:
        #             print("Se detectó una imagen falsa en el video.")
        #         else:
        #             print("Se detectó una imagen verdadero en el video.")

        #         count = 0

        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        aspect_ratio = width / height

        if width < 480 or height < 360 or aspect_ratio > 2.0:
            indice = 0
            print("El video tiene una calidad baja o sospechosa.")
    except Exception as er:
        indice = 0
        print(er)

    cap.release()

    return indice

# Función para verificar si el audio del video tiene características anormales
def verificar_audio_video(video_path):
    text = ''
    indice = 1

    try:
        audio_temp_file = "temp_audio.wav"

        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_temp_file)

        # Transcribir
        r = speech_recognition.Recognizer()
        with speech_recognition.AudioFile(audio_temp_file) as source:
            audio_text = r.record(source)
        text = r.recognize_google(audio_text, language='en-US')

        # Extraer características de audio del video
        audio, sr = librosa.load(audio_temp_file)

        # Calcular la duración y el volumen promedio del audio
        duracion_audio = librosa.get_duration(y=audio, sr=sr)
        volumen_promedio = np.mean(np.abs(audio))

        # Verificar características anormales del audio
        if duracion_audio < 2.0 or volumen_promedio < 0.01:
            indice = 0
            print("El audio del video tiene características anormales.")

        # Eliminar los archivos temporales
        os.remove("temp_audio.wav")
    except Exception as er:
        indice = 0
        print('verificar_audio_video ' + er)
    return text, indice

# Función para analizar el ruido y la compresión en una imagen
def analizar_ruido_compresion(imagen):
    # Convertir la imagen a escala de grises
    imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

    # Calcular la descomposición wavelet de la imagen utilizando la transformada wavelet discreta 2D (DWT)
    coeffs = pywt.dwt2(imagen_gris, 'haar')
    cA, (cH, cV, cD) = coeffs

    # Calcular el coeficiente de detalle máximo para cada dirección (horizontal, vertical y diagonal)
    max_detail_coef = max(abs(cH).max(), abs(cV).max(), abs(cD).max())

    # Calcular la varianza del coeficiente de aproximación (cA)
    approx_var = cA.var()

    # Verificar si hay presencia de ruido o compresión basado en los umbrales establecidos
    umbral_ruido = 10  # Umbral para detectar ruido
    umbral_compresion = 1000  # Umbral para detectar compresión

    if max_detail_coef > umbral_ruido or approx_var < umbral_compresion:
        return True  # La imagen tiene ruido o artefactos de compresión
    else:
        return False  # La imagen parece ser auténtica
    
def rekognition_video_new(video_path):
    aws_access_key_id = 'AKIAWKYR5AY7ET5LCBAL'
    aws_secret_access_key = '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'
    aws_region = 'us-east-1'

    # s3_client = boto3.client('s3',
    #     aws_access_key_id=aws_access_key_id,
    #     aws_secret_access_key=aws_secret_access_key,
    #     region_name=aws_region
    # )

    # video_name = 'nombre_del_video_2.mp4'
    # with open(video_path, 'rb') as video_file:
    #     response =  s3_client.upload_fileobj(video_file, "custom-labels-console-us-east-1-f477297e29", video_name)
    #     print('response:::')
    #     print(response)

    # return True

    rekognition_client = boto3.client('rekognition',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    
    # with open(video_path, 'rb') as video_file:
    #     video = video_file.read()
    #     # print(video)

    response = rekognition_client.start_label_detection(Video={
        'S3Object': {
            'Bucket': 'custom-labels-console-us-east-1-f477297e29',
            'Name': 'nombre_del_video_2.mp4',
        }
    })
    # job_id = response['JobId']
    # print('response::::::::: start_label_detection')
    # print(response)

    # return True

    job_id = "f22e2701eab72eff4733f234c2b569153116e65086e792bc1d7920f9bdc193d6"
    # Obtiene los resultados del análisis del video:
    response = rekognition_client.get_label_detection(JobId=job_id)
    print('response::::::::: get_label_detection')
    print(response['JobStatus'])

    # IN_PROGRESS | SUCCEEDED | FAILED

    labels = response['Labels']
    activities = []
    for label in labels:
        if label['Label']['Name'] not in activities:
            if  label['Label']['Confidence'] > 80:
                activities.append(label['Label']['Name'])
        # print('Label: ', label['Label']['Name'])
        # print('Confidence: ', label['Label']['Confidence'])
    
    for label in activities:
        print('Label: ', label)

    # response_celebrity = rekognition_client.get_celebrity_recognition(JobId=job_id)
    # for celebrity in response_celebrity['Celebrities']:
    #     print(celebrity['Celebrity']['Name'])