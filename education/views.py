from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.db.models import Count, Q, F
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .forms import UserRegistrationForm, ProfileUpdateForm, VideoUploadForm, NoteForm
from .models import UserProfile, VideoContent, Note, Subject, VideoView

def homepage(request):
    # Get featured subjects
    featured_subjects = Subject.objects.annotate(
        video_count=Count('videos', filter=Q(videos__is_published=True))
    ).order_by('-video_count')[:6]
    
    # Get latest videos
    latest_videos = VideoContent.objects.filter(
        is_published=True
    ).select_related('teacher', 'subject').order_by('-created_at')[:8]
    
    # Get popular teachers (teachers with most videos)
    popular_teachers = UserProfile.objects.filter(
        role='teacher',
        is_approved=True
    ).annotate(
        video_count=Count('user__videos', filter=Q(user__videos__is_published=True))
    ).filter(video_count__gt=0).order_by('-video_count')[:4]
    
    context = {
        'featured_subjects': featured_subjects,
        'latest_videos': latest_videos,
        'popular_teachers': popular_teachers,
    }
    return render(request, 'education/homepage.html', context)







@login_required
def profile(request):
    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(request.user, request.POST)
        
        if 'update_profile' in request.POST and user_form.is_valid():
            user_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
            
        elif 'change_password' in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = ProfileUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
    
    context = {
        'user_form': user_form,
        'password_form': password_form,
    }
    
    return render(request, 'registration/profile.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            user_profile = UserProfile.objects.get(user=user)
            if user_profile.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user_profile.role == 'student':
                return redirect('student_dashboard')
    return render(request, 'education/login.html')

@login_required
def teacher_dashboard(request):
    # Ensure only teachers can access this view
    if not hasattr(request.user, 'is_teacher') or not request.user.is_teacher:
        messages.error(request, 'You do not have permission to access the teacher dashboard.')
        return redirect('home')
    
    # Get teacher's data
    from .models import Course, Enrollment  # Import models here to avoid circular imports
    
    # Get teacher's courses
    teacher_courses = Course.objects.filter(teacher=request.user)
    
    # Get students enrolled in teacher's courses
    students = User.objects.filter(
        enrollments__course__in=teacher_courses
    ).distinct()
    
    # Get recent activity (example: recent enrollments, submissions, etc.)
    recent_activity = []  # You can implement this based on your models
    
    context = {
        'courses': teacher_courses,
        'students': students,
        'courses_count': teacher_courses.count(),
        'students_count': students.count(),
        'assignments_count': 0,  # Update this based on your assignment model
        'recent_activity': recent_activity,
    }
    
    return render(request, 'education/teacher/dashboard.html', context)

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'student':
        messages.warning(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get user's enrolled subjects
    user_profile = request.user.userprofile
    enrolled_subjects = user_profile.subjects.all()
    
    # Get recommended videos (from enrolled subjects or popular ones)
    recommended_videos = VideoContent.objects.filter(
        is_published=True,
        subject__in=enrolled_subjects
    ).select_related('teacher', 'subject').order_by('-view_count')[:6]
    
    # If not enough recommended videos, get some popular ones
    if recommended_videos.count() < 6:
        additional = VideoContent.objects.filter(
            is_published=True
        ).exclude(id__in=[v.id for v in recommended_videos])\
            .select_related('teacher', 'subject')\
            .order_by('-view_count')[:6 - recommended_videos.count()]
        recommended_videos = list(recommended_videos) + list(additional)
    
    # Get recently viewed videos
    recently_viewed = VideoView.objects.filter(
        user=request.user
    ).select_related('video', 'video__teacher', 'video__subject')\
        .order_by('-created_at')[:4]
    
    # Get saved videos and notes
    saved_videos = user_profile.saved_videos.all()[:4]
    saved_notes = user_profile.saved_notes.all()[:4]
    
    context = {
        'enrolled_subjects': enrolled_subjects,
        'recommended_videos': recommended_videos,
        'recently_viewed': [view.video for view in recently_viewed],
        'saved_videos': saved_videos,
        'saved_notes': saved_notes,
    }
    return render(request, 'education/student/dashboard.html', context)

@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'teacher':
        messages.warning(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    teacher_profile = request.user.userprofile
    
    # Get teacher's videos with counts
    videos = VideoContent.objects.filter(
        teacher=request.user
    ).select_related('subject').order_by('-created_at')
    video_count = videos.count()
    
    # Get teacher's notes with counts
    notes = Note.objects.filter(
        teacher=request.user
    ).select_related('subject', 'video').order_by('-created_at')
    note_count = notes.count()
    
    # Get recent students (last 5)
    recent_students = User.objects.filter(
        profile__enrolled_courses__teacher=request.user
    ).distinct().order_by('-date_joined')[:5]
    
    # Get recent enrollments
    recent_enrollments = Enrollment.objects.filter(
        course__teacher=request.user
    ).select_related('student', 'course').order_by('-enrolled_at')[:5]
    
    # Get video views analytics
    video_views = VideoView.objects.filter(
        video__teacher=request.user
    ).count()
    
    context = {
        'teacher': request.user,
        'profile': teacher_profile,
        'videos': videos[:5],  # Show only recent 5 videos
        'video_count': video_count,
        'notes': notes[:5],    # Show only recent 5 notes
        'note_count': note_count,
        'recent_students': recent_students,
        'recent_enrollments': recent_enrollments,
        'total_views': video_views,
    }
    
    # Get video statistics
    total_views = sum(video.view_count for video in videos)
    total_videos = videos.count()
    
    # Get recent student activity
    recent_views = VideoView.objects.filter(
        video__teacher=request.user
    ).select_related('user', 'video').order_by('-created_at')[:5]
    
    context = {
        'teacher_profile': teacher_profile,
        'videos': videos[:5],  # Show only recent 5 videos
        'notes': notes[:5],    # Show only recent 5 notes
        'total_views': total_views,
        'total_videos': total_videos,
        'recent_views': recent_views,
    }
    return render(request, 'education/teacher/dashboard.html', context)


class VideoDetailView(DetailView):
    model = VideoContent
    template_name = 'education/video_detail.html'
    context_object_name = 'video'
    
    def get_queryset(self):
        # Only show published videos to non-owners
        queryset = VideoContent.objects.select_related('teacher', 'subject')
        if not self.request.user.is_authenticated or self.request.user != self.get_object().teacher:
            queryset = queryset.filter(is_published=True)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.get_object()
        
        # Track view if user is authenticated
        if self.request.user.is_authenticated:
            VideoView.objects.get_or_create(
                video=video,
                user=self.request.user,
                defaults={'ip_address': self.get_client_ip()}
            )
            video.view_count = F('view_count') + 1
            video.save(update_fields=['view_count'])
            video.refresh_from_db()
        
        # Get related videos (same subject)
        related_videos = VideoContent.objects.filter(
            subject=video.subject,
            is_published=True
        ).exclude(id=video.id).select_related('teacher')[:4]
        
        # Get video notes
        notes = video.video_notes.filter(is_public=True)
        
        # Check if video is saved by user
        is_saved = False
        if self.request.user.is_authenticated:
            is_saved = self.request.user.userprofile.saved_videos.filter(id=video.id).exists()
        
        context.update({
            'related_videos': related_videos,
            'notes': notes,
            'is_saved': is_saved,
        })
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class TeacherProfileView(DetailView):
    model = User
    template_name = 'education/teacher_profile.html'
    context_object_name = 'teacher'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_queryset(self):
        return User.objects.filter(userprofile__role='teacher', userprofile__is_approved=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_object()
        
        # Get teacher's profile
        teacher_profile = teacher.userprofile
        
        # Get teacher's videos (published only for non-owners)
        videos = teacher.videos.all()
        if not self.request.user.is_authenticated or self.request.user != teacher:
            videos = videos.filter(is_published=True)
        
        # Get teacher's subjects (from their videos)
        subjects = Subject.objects.filter(
            videos__teacher=teacher,
            videos__is_published=True
        ).distinct()
        
        # Get teacher's public notes
        notes = teacher.notes.filter(is_public=True).select_related('subject', 'video')[:6]
        
        # Get total views across all videos
        total_views = teacher.videos.aggregate(total_views=Sum('view_count'))['total_views'] or 0
        
        context.update({
            'teacher_profile': teacher_profile,
            'videos': videos.order_by('-created_at')[:8],
            'subjects': subjects,
            'notes': notes,
            'total_views': total_views,
            'total_videos': videos.count(),
            'total_notes': notes.count(),
        })
        return context


@login_required
@require_POST
def toggle_save_video(request, video_id):
    video = get_object_or_404(VideoContent, id=video_id, is_published=True)
    user_profile = request.user.userprofile
    
    if user_profile.saved_videos.filter(id=video_id).exists():
        user_profile.saved_videos.remove(video)
        saved = False
    else:
        user_profile.saved_videos.add(video)
        saved = True
    
    return JsonResponse({'saved': saved})

@login_required
def student_dashboard(request):
    if request.user.userprofile.role != 'student':
        return redirect('homepage')
    
    # Get user's watched videos count (you'll need to implement this logic)
    videos_watched = request.user.watched_videos.count() if hasattr(request.user, 'watched_videos') else 0
    
    # Get user's notes count (you'll need to implement this logic)
    notes_taken = request.user.notes.count() if hasattr(request.user, 'notes') else 0
    
    # Get user's streak (you'll need to implement this logic)
    streak_days = 7  # Example value, implement your own logic
    
    # Get user's achievements count (you'll need to implement this logic)
    achievements = 3  # Example value, implement your own logic
    
    # Sample recent activities (replace with actual data from your models)
    recent_activities = [
        {
            'type': 'video',
            'text': 'You completed watching "Introduction to Python"',
            'time': '2 hours ago',
            'badge': 'New'
        },
        {
            'type': 'note',
            'text': 'You took notes on "Data Structures"',
            'time': '1 day ago'
        },
        {
            'type': 'quiz',
            'text': 'You scored 85% on "Python Basics Quiz"',
            'time': '2 days ago',
            'badge': 'High Score!'
        },
        {
            'type': 'video',
            'text': 'You started "Web Development with Django"',
            'time': '3 days ago'
        }
    ]
    
    # Get recommended videos (you might want to implement a recommendation system)
    recommended_videos = VideoContent.objects.order_by('-created_at')[:4]
    
    context = {
        'stats': {
            'videos_watched': videos_watched,
            'notes_taken': notes_taken,
            'streak_days': streak_days,
            'achievements': achievements,
        },
        'recent_activities': recent_activities,
        'recommended_videos': recommended_videos,
    }
    
    return render(request, 'education/student/dashboard.html', context)