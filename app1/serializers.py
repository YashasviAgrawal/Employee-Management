from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import (
    Client, Project, Task, TimeLog, Feedback, TaskComment,
    Skill, EmployeeProfile, ProjectAssignment,
    TaskStatusHistory, Attendance, AwayLog,
)

User = get_user_model()


# ──────────────────────────────────────────────────────────
#  Auth serializers
# ──────────────────────────────────────────────────────────

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password confirmation."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2',
                  'first_name', 'last_name', 'role')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        # Auto-create EmployeeProfile for employee users
        if user.role == 'EMPLOYEE':
            EmployeeProfile.objects.create(user=user)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login — accepts username and password."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing and updating user profile."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id', 'username', 'role')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password while authenticated."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


# ──────────────────────────────────────────────────────────
#  Admin-only: User management serializer
# ──────────────────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    """Admin can view and manage all users."""
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_active', 'date_joined', 'last_login',
        )
        read_only_fields = ('id', 'date_joined', 'last_login')


# ──────────────────────────────────────────────────────────
#  Skill serializers
# ──────────────────────────────────────────────────────────

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')


# ──────────────────────────────────────────────────────────
#  Employee Profile serializers
# ──────────────────────────────────────────────────────────

class EmployeeProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        write_only=True,
        source='skills',
        required=False,
    )

    class Meta:
        model = EmployeeProfile
        fields = (
            'id', 'user', 'username', 'full_name', 'email',
            'skills', 'skill_ids', 'designation', 'department',
        )
        read_only_fields = ('id', 'user')


# ──────────────────────────────────────────────────────────
#  Client serializers
# ──────────────────────────────────────────────────────────

class ClientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='CLIENT'),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Client
        fields = ('id', 'user', 'company_name', 'contact_person')


# ──────────────────────────────────────────────────────────
#  Project serializers
# ──────────────────────────────────────────────────────────

class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(
        source='client.company_name', read_only=True
    )
    assigned_employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'title', 'client', 'client_name',
            'start_date', 'end_date', 'budget_hours', 'budget_amount',
            'assigned_employee_count',
        )

    def get_assigned_employee_count(self, obj):
        return obj.assignments.count()


class ProjectReadSerializer(serializers.ModelSerializer):
    """Read-only serializer with nested client info (for Client role)."""
    client_name = serializers.CharField(
        source='client.company_name', read_only=True
    )
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'title', 'client_name',
            'start_date', 'end_date', 'task_count',
        )

    def get_task_count(self, obj):
        return obj.tasks.count()


# ──────────────────────────────────────────────────────────
#  Project Assignment serializers
# ──────────────────────────────────────────────────────────

class ProjectAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source='employee.get_full_name', read_only=True
    )
    employee_username = serializers.CharField(
        source='employee.username', read_only=True
    )
    project_title = serializers.CharField(
        source='project.title', read_only=True
    )

    class Meta:
        model = ProjectAssignment
        fields = (
            'id', 'project', 'project_title', 'employee',
            'employee_name', 'employee_username',
            'assigned_date', 'role_in_project',
        )
        read_only_fields = ('id', 'assigned_date')


# ──────────────────────────────────────────────────────────
#  Task serializers
# ──────────────────────────────────────────────────────────

class TaskSerializer(serializers.ModelSerializer):
    """Full task serializer for Admin."""
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True
    )
    project_title = serializers.CharField(
        source='project.title', read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )
    required_skills = SkillSerializer(many=True, read_only=True)
    required_skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        write_only=True,
        source='required_skills',
        required=False,
    )

    class Meta:
        model = Task
        fields = (
            'id', 'project', 'project_title', 'assigned_to',
            'assigned_to_name', 'created_by', 'created_by_name',
            'title', 'description', 'due_date', 'estimated_hours',
            'status', 'required_skills', 'required_skill_ids',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')


class TaskClientSerializer(serializers.ModelSerializer):
    """
    Read-only task view for Client role.
    Hides budget-sensitive fields like estimated_hours.
    """
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True
    )

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'due_date',
            'status', 'assigned_to_name', 'created_at',
        )
        read_only_fields = fields


class EmployeeTaskSerializer(serializers.ModelSerializer):
    """
    Employee can create tasks, update all fields of their own tasks,
    and self-assign unassigned tasks.
    """
    project_title = serializers.CharField(
        source='project.title', read_only=True
    )
    required_skills = SkillSerializer(many=True, read_only=True)
    required_skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        write_only=True,
        source='required_skills',
        required=False,
    )

    class Meta:
        model = Task
        fields = (
            'id', 'project', 'project_title', 'assigned_to',
            'title', 'description', 'due_date', 'estimated_hours',
            'status', 'required_skills', 'required_skill_ids',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


# ──────────────────────────────────────────────────────────
#  Task Status History serializers
# ──────────────────────────────────────────────────────────

class TaskStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(
        source='changed_by.get_full_name', read_only=True
    )
    task_title = serializers.CharField(
        source='task.title', read_only=True
    )

    class Meta:
        model = TaskStatusHistory
        fields = (
            'id', 'task', 'task_title', 'changed_by', 'changed_by_name',
            'old_status', 'new_status', 'changed_at', 'notes',
        )
        read_only_fields = ('id', 'changed_by', 'changed_at')


# ──────────────────────────────────────────────────────────
#  TimeLog serializers
# ──────────────────────────────────────────────────────────

class TimeLogSerializer(serializers.ModelSerializer):
    duration_hours = serializers.FloatField(read_only=True)
    task_title = serializers.CharField(
        source='task.title', read_only=True
    )
    username = serializers.CharField(
        source='user.username', read_only=True
    )

    class Meta:
        model = TimeLog
        fields = (
            'id', 'user', 'username', 'task', 'task_title',
            'start_time', 'end_time', 'duration_hours',
        )
        read_only_fields = ('id', 'duration_hours')


class EmployeeTimeLogSerializer(serializers.ModelSerializer):
    """Employee creates time logs — user is auto-set to the request user."""
    duration_hours = serializers.FloatField(read_only=True)
    task_title = serializers.CharField(
        source='task.title', read_only=True
    )

    class Meta:
        model = TimeLog
        fields = (
            'id', 'task', 'task_title',
            'start_time', 'end_time', 'duration_hours',
        )
        read_only_fields = ('id', 'start_time', 'end_time', 'duration_hours')

    def validate_task(self, value):
        """Ensure the employee is assigned to this task."""
        request = self.context.get('request')
        if request and value.assigned_to != request.user:
            raise serializers.ValidationError(
                "You can only log time for tasks assigned to you."
            )
        return value


# ──────────────────────────────────────────────────────────
#  Attendance serializers
# ──────────────────────────────────────────────────────────

class AwayLogSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.FloatField(read_only=True)

    class Meta:
        model = AwayLog
        fields = ('id', 'away_start', 'away_end', 'duration_minutes')
        read_only_fields = ('id',)


class AttendanceSerializer(serializers.ModelSerializer):
    """Full attendance serializer with computed fields."""
    away_logs = AwayLogSerializer(many=True, read_only=True)
    total_away_hours = serializers.FloatField(read_only=True)
    total_working_hours = serializers.FloatField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = (
            'id', 'user', 'username', 'full_name', 'date',
            'sign_in_time', 'sign_out_time', 'status',
            'away_logs', 'total_away_hours', 'total_working_hours',
        )
        read_only_fields = (
            'id', 'user', 'date', 'sign_in_time', 'sign_out_time',
            'status', 'total_away_hours', 'total_working_hours',
        )


class AttendanceAdminSerializer(serializers.ModelSerializer):
    """Admin view with all employee info."""
    away_logs = AwayLogSerializer(many=True, read_only=True)
    total_away_hours = serializers.FloatField(read_only=True)
    total_working_hours = serializers.FloatField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = (
            'id', 'user', 'username', 'full_name', 'date',
            'sign_in_time', 'sign_out_time', 'status',
            'away_logs', 'total_away_hours', 'total_working_hours',
        )
        read_only_fields = ('id',)


# ──────────────────────────────────────────────────────────
#  Feedback serializers
# ──────────────────────────────────────────────────────────

class FeedbackSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(
        source='project.title', read_only=True
    )

    class Meta:
        model = Feedback
        fields = ('id', 'project', 'project_title', 'rating', 'comment')


# ──────────────────────────────────────────────────────────
#  TaskComment serializers
# ──────────────────────────────────────────────────────────

class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source='author.get_full_name', read_only=True
    )
    author_role = serializers.CharField(
        source='author.role', read_only=True
    )

    class Meta:
        model = TaskComment
        fields = (
            'id', 'task', 'author', 'author_name', 'author_role',
            'content', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'task', 'author', 'created_at', 'updated_at')
