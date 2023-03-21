from django.shortcuts import render, redirect
from django.contrib import messages
from validate_email import validate_email
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse

def register(request):

    if request.method == "POST":
        context = {'has_error': False, 'data':request.POST}
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if len(password)<6:
            messages.add_message(request, messages.WARNING, "The password entered is too short")

            context['has_error'] = True
        
        if password != password2:
            messages.add_message(request, messages.WARNING, "The passwords entered do not match!")

            context['has_error'] = True

        if not validate_email(email):
            messages.add_message(request, messages.WARNING, "Enter a valid email")

            context['has_error'] = True

        if not username:
            messages.add_message(request, messages.WARNING, "Enter your username!")

            context['has_error'] = True

        if User.objects.filter(username = username).exists():
            messages.add_message(request, messages.WARNING, "Username taken, please choose another one")

        if User.objects.filter(email = email).exists():
            messages.add_message(request, messages.WARNING, "Email exists in our database, please use another one")

        if context['has_error']:
            return render(request, 'registration/register.html', context)
        
        user = User.objects.create_user(username=username, email=email)
        user.set_password(password)
        user.save()
        messages.add_message(request, messages.SUCCESS, "Registration Succesful! You may login")

        return redirect('login')
    
    return render(request, 'registration/register.html')


    

def login_user(request):

    if request.method == 'POST':
        context = {'data': request.POST}
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)


        if not user:
            messages.add_message(request, messages.WARNING, 'Invalid credentials')

            return render(request, 'registration/login.html', context)
        
        login(request, user)
        messages.add_message(request, messages.WARNING, f'Welcome {user.username}')
        return redirect(reverse('homepage'))


    return render(request, 'registration/login.html')

def logout_user(request):

    logout(request)
    messages.add_message(request, messages.INFO, 'Successfully logged out!')

    return redirect(reverse('login'))