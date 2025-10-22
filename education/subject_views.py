from django.views.generic import ListView, DetailView
from django.db.models import Count, Q
from .models import Subject, VideoContent

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
