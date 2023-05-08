"""fakenews URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from fakenews.controllers import site, new, dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', site.login),
    path('login/', site.login),
    path('login/<int:code>/', site.login),
    path('signup/', site.signup),
    path('logout/', site.logout),
    path('index/', site.index),
    path('new/list/', new.list),
    path('new/create/', new.create),
    path('new/detail/<int:pk>/', new.detail),
    path('new/public/state/', new.public_change),
    path('dashboard/', dashboard.chart),
    path('dashboard/data/<int:option>/', dashboard.get_data),
]
