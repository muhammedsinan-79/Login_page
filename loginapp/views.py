from django.shortcuts import render , redirect
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.core.cache import cache
from .models import RateLimitLog , InvalidCredentialsLog
from .throttle import EmailRateThrottle, ForgotPasswordEmailThrottle,IpRateLimiting
from .models import RateLimitLog
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import Throttled


# Create your views here.

class HomePage(APIView):
    def get(self, request):
        return render(request,'home.html')
        
class SignupPage(APIView):
    def get(self,request):
        return render(request,'signup.html')
    
    def post(self,request):

        print("incoming data:" , request.data)
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('full_name')
        confirm_password = request.data.get('confirm_password')

        if password != confirm_password:
            #return Response({'error': 'Passwords do not match'}, status=400)
            messages.error(request,"Passwords do not match")
            return redirect('/signup/')
        
        if User.objects.filter(username=email).exists():
            #return Response({'error':'User already exists'},status =400)
            messages.success(request, "User already exists , Please log in.")
            return redirect('/login/')
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )
        Token.objects.create(user=user)
        messages.success(request, "Your account has been created successfully. Please log in.")
        return redirect('/login/')
        #return render(request, 'login_success.html', {'email': email})
     
class LoginPage(APIView):

    throttle_classes = [EmailRateThrottle]

    def handle_exception(self, exc,): #this method is for displaying throttled message in template
        if isinstance(exc, Throttled):
            wait_time = exc.wait
            email = self.request.POST.get("email")
            print(email)

            return render(self.request, 'login.html', {
                "error": f"many attempt . Try again in {wait_time} seconds."
            })
        return super().handle_exception(exc)
    

    def get(self,request): 
        return render(request , 'login.html')
    
    def post(self , request):

        email = request.data.get('email')
        password = request.data.get('password')
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        user = authenticate(username=email ,password=password)
        if user:
            token,_=Token.objects.get_or_create(user=user)
            return render(request, 'login_success.html', {'email': email, 'token': token.key})
        else:
            #return Response({"message":"Invalid credentials"},status=400)

            InvalidCredentialsLog.objects.create(email=email ,ip_address = ip , user_agent=user_agent )

            messages.error(request, "Invalid credentials")
            return redirect('/login/')

from rest_framework.authtoken.models import Token

class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("User:", request.user)
        print("Token:", request.META.get('HTTP_AUTHORIZATION'))
        print("Is authenticated:", request.user.is_authenticated)

        try:
            token = request.user.auth_token
            token.delete()
            return Response({"message": "Logout successful."})
        except Token.DoesNotExist:
            return Response({"error": "Token not found or already deleted."}, status=400)
        except Exception as e:
            print("Logout failed:", e)
            return Response({"error": "Logout failed."}, status=400)

class ForgotPasswordView(APIView):
    throttle_classes = [ForgotPasswordEmailThrottle,IpRateLimiting]

    def handle_exception(self, exc): #this method is for displaying throttled message in template
        
        if isinstance(exc, Throttled): 
            wait_time = exc.wait
            email = self.request.POST.get('email')
            cache_key = f"password_reset_rate_limit:{email}"
            cache.set(cache_key,True,60)
            return render(self.request, 'forgot_password.html', {
                "error": f"Too many requests. Try again in {wait_time} seconds."
            })
        return super().handle_exception(exc)
    
    def get(self,request):
        return render(request, 'forgot_password.html')
    
    def post(self,request):
        email = request.data.get('email')
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://127.0.0.1:8000/reset-password/{uid}/{token}/"

            send_mail (
                subject="Reset Your Password",
                message=f"Click the link to reset your password: {reset_link}",
                from_email="muhammedsinaan78@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
            #return Response({"message": "Password reset email sent."})

            messages.success(request, "Password reset email sent.")
            return redirect('/login/')

        except User.DoesNotExist:
             RateLimitLog.objects.create(
                email=email,
                ip_address=ip,
                user_agent=user_agent
            )
             return render(request, 'forgot_password.html', {
                'error': "If this email exists, a reset link has been sent."
            })
        
        except Exception as e:
            print(f"Error sending email: {e}")
            return render(request, 'forgot_password.html', {
                'error': "An error occurred. Please try again later."
            })
              
class ResetPasswordView(APIView):
    def get(self, request, uidb64, token):
        # You can add any validation here if needed
        return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})

    def post(self,request ,uidb64,token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user,token):
                new_password = request.data.get("password")
                user.set_password(new_password)
                user.save()

                messages.success(request, "Your password has been changed successfully. Please log in.")
                return redirect('/login/')


                #return Response({"message": "Password reset successful."})
            else:
                return render(request, 'reset_password.html', {
                    'error': "Invalid or expired token.",
                    'uidb64': uidb64,
                    'token': token,})
        except Exception as e:
            print("Reset error:", e)
            return render(request, 'reset_password.html', {
                'uidb64': uidb64,
                'token': token,
                'error': "Something went wrong."
            })
        


       


         


        
