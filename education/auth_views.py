from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm

def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Set the user as a teacher (assuming your form has an is_teacher field)
            if hasattr(form, 'cleaned_data') and 'is_teacher' in form.cleaned_data:
                user.is_teacher = form.cleaned_data['is_teacher']
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            # Redirect to teacher dashboard if user is a teacher
            if hasattr(user, 'is_teacher') and user.is_teacher:
                return redirect('teacher_dashboard')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'Welcome back, {username}!')
                # Redirect to teacher dashboard if user is a teacher, otherwise to home
                if hasattr(user, 'is_teacher') and user.is_teacher:
                    return redirect('teacher_dashboard')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')
