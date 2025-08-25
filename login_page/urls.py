"""
URL configuration for login_page project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from loginapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.LoginPage.as_view()),
    path('login/',views.LoginPage.as_view()), #using a class-based view (APIView), so you need to call .as_view()
    path('signup/',views.SignupPage.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('forgot-password/', views.ForgotPasswordView.as_view()),
    path('reset-password/<uidb64>/<token>/', views.ResetPasswordView.as_view()),

]
