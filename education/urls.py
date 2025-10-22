from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from . import auth_views as custom_auth_views
from .views import teacher_dashboard
from .views import VideoDetailView, TeacherProfileView
from .subject_views import SubjectListView, SubjectDetailView

urlpatterns = [
    # Homepage
    path('', views.homepage, name='home'),
    
    # Authentication URLs
    path('signup/', custom_auth_views.signup_view, name='signup'),
    path('login/', custom_auth_views.login_view, name='login'),
    path('logout/', custom_auth_views.logout_view, name='logout'),
    
    # Teacher Dashboard
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    
    # Include Django's auth URLs for password reset functionality
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Dashboard URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    
    # Password Change
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='registration/password_change.html'
         ),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='registration/password_change_done.html'
         ),
         name='password_change_done'),
         
    # Video and Teacher URLs
    path('videos/<int:pk>/<slug:slug>/', VideoDetailView.as_view(), name='video_detail'),
    path('teacher/<str:username>/', TeacherProfileView.as_view(), name='teacher_profile'),
    path('api/toggle-save-video/<int:video_id>/', views.toggle_save_video, name='toggle_save_video'),
    
    # Subject listing
    path('subjects/', SubjectListView.as_view(), name='subject_list'),
    path('subjects/<slug:slug>/', SubjectDetailView.as_view(), name='subject_detail'),
]