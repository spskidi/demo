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

# ... [rest of your existing view functions] ...

class SubjectListView(ListView):
    model = Subject
    template_name = 'education/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Subject.objects.annotate(
            video_count=Count('videos', filter=Q(videos__is_published=True))
        ).filter(video_count__gt=0).order_by('name')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'All Subjects'
        return context


class SubjectDetailView(DetailView):
    model = Subject
    template_name = 'education/subject_detail.html'
    context_object_name = 'subject'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Subject.objects.annotate(
            video_count=Count('videos', filter=Q(videos__is_published=True))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject = self.get_object()
        
        # Get published videos for this subject
        videos = subject.videos.filter(is_published=True).select_related('teacher')
        
        # Get related subjects (excluding current subject)
        related_subjects = Subject.objects.filter(
            category=subject.category
        ).exclude(id=subject.id).annotate(
            video_count=Count('videos', filter=Q(videos__is_published=True))
        ).filter(video_count__gt=0)[:4]
        
        context.update({
            'videos': videos,
            'related_subjects': related_subjects,
            'page_title': f"{subject.name} - Videos"
        })
        return context
