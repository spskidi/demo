from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
import os

def video_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/videos/teacher_<id>/<filename>
    return os.path.join('videos', f"teacher_{instance.teacher.id}", filename)

def note_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/notes/teacher_<id>/<filename>
    return os.path.join('notes', f"teacher_{instance.teacher.id}", filename)

def thumbnail_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/thumbnails/teacher_<id>/<filename>
    return os.path.join('thumbnails', f"teacher_{instance.teacher.id}", filename)

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to='subject_thumbnails/', blank=True, null=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('subject_detail', kwargs={'slug': self.slug})


class VideoContent(models.Model):
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    video_file = models.FileField(
        upload_to=video_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'mov', 'avi'])]
    )
    thumbnail = models.ImageField(upload_to=thumbnail_upload_path, blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Duration in seconds", default=0)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='videos')
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_LEVELS, default='beginner')
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Video Lecture'
        verbose_name_plural = 'Video Lectures'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{self.id or ''}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('video_detail', kwargs={'slug': self.slug, 'pk': self.id})
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    @property
    def duration_formatted(self):
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"


class VideoView(models.Model):
    video = models.ForeignKey('VideoContent', on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['video', 'user']),
            models.Index(fields=['video', 'session_key']),
        ]
    
    def __str__(self):
        return f"View of {self.video.title} by {self.user.username if self.user else 'Anonymous'}"


class Note(models.Model):
    NOTE_TYPES = [
        ('video', 'Video Notes'),
        ('lecture', 'Lecture Notes'),
        ('summary', 'Summary'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    note_type = models.CharField(max_length=10, choices=NOTE_TYPES, default='other')
    file = models.FileField(upload_to=note_upload_path, blank=True, null=True)
    video = models.ForeignKey('VideoContent', on_delete=models.CASCADE, related_name='video_notes', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='subject_notes')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.video:
            return f"Notes for {self.video.title}"
        elif self.subject:
            return f"{self.title} - {self.subject.name}"
        return self.title
    
    def get_absolute_url(self):
        return reverse('note_detail', kwargs={'pk': self.id})


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Student specific fields
    grade = models.CharField(max_length=20, blank=True)
    subjects = models.ManyToManyField(Subject, related_name='students', blank=True)
    saved_videos = models.ManyToManyField('VideoContent', related_name='saved_by', blank=True)
    saved_notes = models.ManyToManyField('Note', related_name='saved_by', blank=True)
    
    # Teacher specific fields
    experience = models.PositiveIntegerField(default=0, help_text="Years of teaching experience")
    qualification = models.CharField(max_length=255, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    
    # Social links
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True)
    youtube = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    def get_absolute_url(self):
        return reverse('profile', kwargs={'username': self.user.username})
    
    def get_teacher_videos(self):
        if self.is_teacher:
            return self.user.videos.all().order_by('-created_at')
        return VideoContent.objects.none()
    
    def get_teacher_notes(self):
        if self.is_teacher:
            return self.user.notes.all().order_by('-created_at')
        return Note.objects.none()


# Signal to automatically create a UserProfile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# Signal to save the UserProfile whenever the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Use get_or_create to ensure we have a profile
    profile, created = UserProfile.objects.get_or_create(user=instance)
    profile.save()