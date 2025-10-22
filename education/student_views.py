from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import UserProfile, TeacherProfile, Subject, VideoContent, Note

@login_required
def student_dashboard(request):
    if not request.user.profile.is_student:
        return redirect('homepage')
    
    # Get recent videos
    recent_videos = VideoContent.objects.filter(is_published=True).order_by('-created_at')[:6]
    
    # Get recommended videos (in a real app, this would be based on user's interests/behavior)
    recommended_videos = VideoContent.objects.filter(is_published=True).order_by('?')[:4]
    
    # Get all subjects for the filter
    subjects = Subject.objects.all()
    
    context = {
        'recent_videos': recent_videos,
        'recommended_videos': recommended_videos,
        'subjects': subjects,
    }
    return render(request, 'education/student_dashboard.html', context)

def search_teachers(request):
    query = request.GET.get('q', '')
    subject_id = request.GET.get('subject', '')
    
    teachers = User.objects.filter(profile__role='teacher', teacher_profile__is_approved=True)
    
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(teacher_profile__bio__icontains=query)
        )
    
    if subject_id:
        teachers = teachers.filter(teacher_profile__subjects__id=subject_id)
    
    # Get all subjects for the filter
    subjects = Subject.objects.all()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(teachers, 10)  # Show 10 teachers per page
    
    try:
        teachers = paginator.page(page)
    except PageNotAnInteger:
        teachers = paginator.page(1)
    except EmptyPage:
        teachers = paginator.page(paginator.num_pages)
    
    context = {
        'teachers': teachers,
        'subjects': subjects,
        'search_query': query,
        'selected_subject': int(subject_id) if subject_id else None,
    }
    return render(request, 'education/teacher_search.html', context)

def teacher_profile(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, profile__role='teacher')
    teacher_profile = get_object_or_404(TeacherProfile, user=teacher)
    
    # Get teacher's videos
    videos = VideoContent.objects.filter(teacher=teacher, is_published=True).order_by('-created_at')
    
    context = {
        'teacher': teacher,
        'teacher_profile': teacher_profile,
        'videos': videos,
    }
    return render(request, 'education/teacher_profile.html', context)

def video_detail(request, video_id):
    video = get_object_or_404(VideoContent, id=video_id, is_published=True)
    
    # Increment view count
    video.view_count += 1
    video.save()
    
    # Get related videos (videos from the same subject)
    related_videos = VideoContent.objects.filter(
        subject=video.subject,
        is_published=True
    ).exclude(id=video.id).order_by('?')[:4]
    
    # Get notes for this video
    notes = Note.objects.filter(video=video)
    
    context = {
        'video': video,
        'related_videos': related_videos,
        'notes': notes,
    }
    return render(request, 'education/video_detail.html', context)
