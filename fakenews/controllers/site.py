from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect
from fakenews.encrypt import Encrypt
from fakenews.models import Rol, User
import requests
import json

@never_cache
def login(request, code=None):
    # Valida si ya inicio sesión
    if 'user' in request.session:
        return HttpResponseRedirect("/index/")
    response = {}
    response['email'] = ''
    if request.method == "POST":
        data = request.POST
        if 'password' in data and 'email' in data:
            if data['email'] != '' and data['password'] != '':
                password = data['password']
                email = data['email']
                response['email'] = email
                response['status'] = 'recaptcha'

                if 'g-recaptcha-response' in request.POST and request.POST['g-recaptcha-response'] != '':
                    recaptcha = request.POST['g-recaptcha-response']
                    url = 'https://www.google.com/recaptcha/api/siteverify'
                    myobj = {
                        'secret': '6LcGEholAAAAAJMPTmE1VzgEWeQk3K5OcyeU4Q-4',
                        'response': recaptcha
                    }

                    response_google = requests.post(url, data=myobj)
                    response_api = json.loads(response_google.text)

                    if response_api['success'] == True:
                        try:
                            user_val = User.objects.get(email=email)
                            if Encrypt().verify(password, user_val.password):
                                response['status'] = 'success'
                                response['message'] = 'Login exitoso'
                                request.session['user'] = {
                                    'id': user_val.id,
                                    'name': user_val.name,
                                    'email': user_val.email,
                                    'rol': user_val.rol_id,
                                    'rol_name': user_val.rol.name,
                                }
                                response['session'] = request.session['user']
                                return HttpResponseRedirect('/index/')
                            else:
                                response['status'] = 'fail'
                                response['message'] = 'Clave incorrecta'
                        except User.DoesNotExist:
                            response['status'] = 'fail'
                            response['message'] = 'El usuario no existe' 
    elif code == 1:
        response['status'] = 'success'
        response['message'] = 'El usuario fue registrado con exito'
        return render(request, 'site/login.html', context=response)
                    
    return render(request, 'site/login.html', context=response)

def logout(request):
    if 'user' in request.session:
        del request.session['user']
    return HttpResponseRedirect('/login/')

@never_cache
def signup(request):
    response = {}
    data_form =  {'name': '', 'email': ''}
    if request.method == "POST":
        data = request.POST
        if 'name' in data and 'email' in data and 'password' in data:
            if data['name'] != '' and data['email'] != '' and data['password'] != '':
                name = data['name']
                email = data['email']
                password = data['password']

                data_form =  {
                    'name': name,
                    'email': email,
                }

                # Se verifica que el usuario no exista.
                if not User.objects.filter(email=email):
                    # En caso de que no exista el rol, se verifica y crea.
                    try:
                        Rol.objects.get(id=2)
                    except Rol.DoesNotExist:
                        new_rol = Rol()
                        new_rol.id = 2
                        new_rol.name = "Usuario"
                        new_rol.description = "Usuario"
                        new_rol.save()

                    password_encrypt = Encrypt().encrypt_code(password)
                    new_user = User()
                    new_user.name = name
                    new_user.email = email
                    new_user.rol_id = 2
                    new_user.password = password_encrypt
                    new_user.save()
                    response['status'] = 'success'
                    
                    # recipient_list = [new_user.email,]
                    # Email().welcome(recipient_list)

                    return HttpResponseRedirect('/login/1/')
                else:
                    response['status'] = 'fail'
                    response['message'] = 'El usuario ya existe'

    response['data'] = data_form
    return render(request, 'site/signup.html', context=response)

def index(request):
    if 'user' in request.session:
        if request.method == "POST":
            print('POST ----')
        return render(request, 'site/index.html', context={'session': request.session['user']})
    else:
        return HttpResponseRedirect('/login/')