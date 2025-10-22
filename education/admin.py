# filepath: edtech_project/education/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Subject, VideoContent, Note, UserProfile, VideoView

# Unregister the default User admin
admin.site.unregister(User)

# Create an inline admin descriptor for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

# Define a new User admin
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_select_related = ('profile', )

    def get_role(self, instance):
        return instance.profile.role if hasattr(instance, 'profile') else 'N/A'
    get_role.short_description = 'Role'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# Register the new User admin
admin.site.register(User, CustomUserAdmin)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(VideoContent)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'subject', 'is_published', 'view_count', 'created_at')
    list_filter = ('is_published', 'subject', 'difficulty', 'created_at')
    search_fields = ('title', 'description', 'teacher__username')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('teacher', 'subject')

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'note_type', 'teacher', 'is_public', 'created_at')
    list_filter = ('note_type', 'is_public', 'created_at')
    search_fields = ('title', 'content', 'teacher__username')
    raw_id_fields = ('video', 'subject', 'teacher')

@admin.register(VideoView)
class VideoViewAdmin(admin.ModelAdmin):
    list_display = ('video', 'user', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('video__title', 'user__username', 'ip_address')
    raw_id_fields = ('video', 'user')