from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Client, Project, Task, TimeLog, Feedback, TaskComment,
    Skill, EmployeeProfile, ProjectAssignment,
    TaskStatusHistory, Attendance, AwayLog,
)


class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'role', 'is_active',
    )
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'department')
    search_fields = ('user__username', 'designation', 'department')
    filter_horizontal = ('skills',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'user')
    search_fields = ('company_name', 'contact_person')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'start_date', 'end_date')
    list_filter = ('client',)
    search_fields = ('title',)


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('project', 'employee', 'role_in_project', 'assigned_date')
    list_filter = ('role_in_project', 'project')
    search_fields = ('project__title', 'employee__username')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'project', 'assigned_to', 'created_by',
        'status', 'due_date',
    )
    list_filter = ('status', 'project')
    search_fields = ('title',)
    filter_horizontal = ('required_skills',)


@admin.register(TaskStatusHistory)
class TaskStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'task', 'old_status', 'new_status', 'changed_by', 'changed_at',
    )
    list_filter = ('new_status',)
    search_fields = ('task__title',)
    readonly_fields = ('changed_at',)


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'start_time', 'end_time')
    list_filter = ('user',)


class AwayLogInline(admin.TabularInline):
    model = AwayLog
    extra = 0
    readonly_fields = ('duration_minutes',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date', 'sign_in_time', 'sign_out_time',
        'status', 'total_working_hours',
    )
    list_filter = ('status', 'date')
    search_fields = ('user__username',)
    inlines = [AwayLogInline]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('project', 'rating')
    list_filter = ('project',)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('author',)


admin.site.register(User, CustomUserAdmin)
