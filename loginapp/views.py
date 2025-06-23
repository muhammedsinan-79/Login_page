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
from .models import RateLimitLog



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
            return Response({'error': 'Passwords do not match'}, status=400)
        

        if User.objects.filter(username=email).exists():
            return Response({'error':'User already exists'},status =400)
        
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
    def get(self,request): 
        return render(request , 'login.html')
    
    def post(self , request):

        email = request.data.get('user_email')
        password = request.data.get('password')

        user = authenticate(username=email ,password=password)
        if user:
            token,_=Token.objects.get_or_create(user=user)
            return render(request, 'login_success.html', {'email': email, 'token': token.key})
        else:
            return Response({'error':'Invalid credentials'},status=400)

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
    def get(self,request):

        return render(request, 'forgot_password.html')
    
    def post(self,request):

        email = request.data.get('email')
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        #rate limting 

        cache_key = f"password_reset_rate_limit:{email}"
        ip_key = f"ip_rate_limit:{ip}"


        email_ttl = 60
        ip_ttl  = 600
        ip_limit_count = 5

        if cache.get(cache_key):
            RateLimitLog.objects.create(email=email,ip_address=ip,user_agent=user_agent)

            try:
                ttl = cache.ttl(cache_key)
            except (AttributeError,NotImplementedError):
                ttl = email_ttl     # fallback default(ttl redis)

            return render(request , 'forgot_password.html',{
                'error': f"Too many requests for this email. Try again in {ttl} seconds.",
                'remaining_time': ttl
            })
        
        ip_count = cache.get(ip_key, 0)
        if ip_count >= ip_limit_count:
            RateLimitLog.objects.create(email=email,ip_address=ip,user_agent=user_agent)
            return render (request , 'forgot_password.html',{
                'error':f"Too many requests from this IP address. Please wait 10 min."
            })
        

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"https://web-production-4d8c4.up.railway.app/reset-password/{uid}/{token}/"

            send_mail (
                subject="Reset Your Password",
                message=f"Click the link to reset your password: {reset_link}",
                from_email="muhammedsinaan78@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )

            #set rate limit key for 60 seconds

            cache.set(cache_key, True, timeout = email_ttl)

            #Increment Ip count
            
            if cache.get(ip_key):
                cache.incr(ip_key)
            else:
                cache.set(ip_key,1,timeout=ip_ttl)    


            messages.success(request, "Password reset email sent.")
            return redirect('/login/')

            #return Response({"message": "Password reset email sent."})
        except User.DoesNotExist:
            return render(request, 'forgot_password.html', {'error': "User not found."})
           
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
        











'''        try:
            user = SignupInfo.objects.get(user_email=email)
        except SignupInfo.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=400)

        if check_password(password, user.user_password):
            # Generate or get existing token
            token, created = Token.objects.get_or_create(user=user)
            return render(request,'login_success.html',{'email':email , 'token': token.key})
        else:
            return Response({'error': 'Invalid password'}, status=400)'''

       


         


        
