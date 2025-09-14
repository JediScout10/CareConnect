# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, MentalHealthTest, ActionPlan, UserCompletedAction, MoodEntry

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'name', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )

@admin.register(MentalHealthTest)
class MentalHealthTestAdmin(admin.ModelAdmin):
    list_display = ('user', 'test_type', 'score', 'category', 'date_taken')
    list_filter = ('test_type', 'category', 'date_taken')
    search_fields = ('user__email', 'user__name')
    ordering = ('-date_taken',)

@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')
    list_filter = ('category',)
    search_fields = ('title', 'category')
    ordering = ('category',)

@admin.register(UserCompletedAction)
class UserCompletedActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_text', 'status', 'completed_at')
    list_filter = ('status', 'completed_at')
    search_fields = ('user__email', 'user__name', 'action_text')
    ordering = ('-completed_at',)

@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood', 'date', 'social_interaction')
    list_filter = ('mood', 'date', 'social_interaction')
    search_fields = ('user__email', 'user__name')
    ordering = ('-date',)

