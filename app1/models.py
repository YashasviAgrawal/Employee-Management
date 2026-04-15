from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('EMPLOYEE', 'Employee'),
        ('CLIENT', 'Client'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_employee(self):
        return self.role == 'EMPLOYEE'

    @property
    def is_client(self):
        return self.role == 'CLIENT'

    def __str__(self):
        return f"{self.username} ({self.role})"


# ──────────────────────────────────────────────────────────
#  Skills
# ──────────────────────────────────────────────────────────

class Skill(models.Model):
    """Reusable skill tags (e.g. Python, React, UI/UX)."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────────────────
#  Employee Profile (skills, designation, department)
# ──────────────────────────────────────────────────────────

class EmployeeProfile(models.Model):
    """Extended profile for employees — stores skills, designation, etc."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        limit_choices_to={'role': 'EMPLOYEE'},
    )
    skills = models.ManyToManyField(Skill, blank=True, related_name='employees')
    designation = models.CharField(max_length=255, blank=True, default='')
    department = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"{self.user.username} — {self.designation or 'Employee'}"


# ──────────────────────────────────────────────────────────
#  Client
# ──────────────────────────────────────────────────────────

class Client(models.Model):
    """
    Client organization. Linked to a User account with role=CLIENT.
    A client user can only see projects belonging to their Client entity.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_profile',
        null=True,
        blank=True,
        limit_choices_to={'role': 'CLIENT'},
    )
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)

    def __str__(self):
        return self.company_name


# ──────────────────────────────────────────────────────────
#  Project
# ──────────────────────────────────────────────────────────

class Project(models.Model):
    title = models.CharField(max_length=255)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='projects'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    budget_hours = models.FloatField()
    budget_amount = models.FloatField()

    def __str__(self):
        return self.title


# ──────────────────────────────────────────────────────────
#  Project ↔ Employee Assignment
# ──────────────────────────────────────────────────────────

class ProjectAssignment(models.Model):
    """
    Admin assigns employees to projects.
    Once assigned, the employee can create/manage tasks in that project.
    """
    ROLE_CHOICES = (
        ('DEVELOPER', 'Developer'),
        ('LEAD', 'Lead'),
        ('TESTER', 'Tester'),
        ('DESIGNER', 'Designer'),
        ('OTHER', 'Other'),
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='assignments'
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_assignments',
        limit_choices_to={'role': 'EMPLOYEE'},
    )
    assigned_date = models.DateField(auto_now_add=True)
    role_in_project = models.CharField(
        max_length=50, choices=ROLE_CHOICES, default='DEVELOPER'
    )

    class Meta:
        unique_together = ('project', 'employee')

    def __str__(self):
        return f"{self.employee.username} → {self.project.title}"


# ──────────────────────────────────────────────────────────
#  Task
# ──────────────────────────────────────────────────────────

class Task(models.Model):
    STATUS_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='tasks'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        limit_choices_to={'role': 'EMPLOYEE'},
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_tasks',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=250)
    description = models.TextField()
    due_date = models.DateField()
    estimated_hours = models.FloatField()
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='TODO'
    )
    required_skills = models.ManyToManyField(
        Skill, blank=True, related_name='tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


# ──────────────────────────────────────────────────────────
#  Task Status History (Day-wise audit trail)
# ──────────────────────────────────────────────────────────

class TaskStatusHistory(models.Model):
    """Tracks every status change on a task for day-wise reporting."""
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='status_history'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_status_changes',
    )
    old_status = models.CharField(max_length=50, blank=True, default='')
    new_status = models.CharField(max_length=50)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = 'Task status histories'

    def __str__(self):
        return f"{self.task.title}: {self.old_status} → {self.new_status}"


# ──────────────────────────────────────────────────────────
#  Time Log
# ──────────────────────────────────────────────────────────

class TimeLog(models.Model):
    """Employees log time against tasks they are assigned to."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_logs',
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='time_logs'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    @property
    def duration_hours(self):
        """Returns duration in hours, or None if not yet ended."""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 2)
        return None

    def __str__(self):
        return f"{self.user.username} — {self.task.title}"


# ──────────────────────────────────────────────────────────
#  Attendance (Sign-in / Sign-out / Away)
# ──────────────────────────────────────────────────────────

class Attendance(models.Model):
    """Daily attendance record for an employee."""
    STATUS_CHOICES = (
        ('SIGNED_IN', 'Signed In'),
        ('AWAY', 'Away'),
        ('SIGNED_OUT', 'Signed Out'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        limit_choices_to={'role': 'EMPLOYEE'},
    )
    date = models.DateField(default=timezone.now)
    sign_in_time = models.DateTimeField()
    sign_out_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='SIGNED_IN'
    )

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    @property
    def total_away_hours(self):
        """Sum of all away durations for this day."""
        total_seconds = 0
        for log in self.away_logs.all():
            if log.away_end:
                delta = log.away_end - log.away_start
                total_seconds += delta.total_seconds()
        return round(total_seconds / 3600, 2)

    @property
    def total_working_hours(self):
        """Total working hours = (sign_out - sign_in) - total_away_time."""
        if not self.sign_out_time:
            # Still signed in — calculate up to now
            end = timezone.now()
        else:
            end = self.sign_out_time
        total = (end - self.sign_in_time).total_seconds() / 3600
        working = total - self.total_away_hours
        return round(max(working, 0), 2)

    def __str__(self):
        return f"{self.user.username} — {self.date} ({self.status})"


class AwayLog(models.Model):
    """Tracks individual away periods within a single attendance day."""
    attendance = models.ForeignKey(
        Attendance, on_delete=models.CASCADE, related_name='away_logs'
    )
    away_start = models.DateTimeField()
    away_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['away_start']

    @property
    def duration_minutes(self):
        if self.away_end:
            delta = self.away_end - self.away_start
            return round(delta.total_seconds() / 60, 1)
        return None

    def __str__(self):
        return f"Away: {self.away_start} → {self.away_end or 'ongoing'}"


# ──────────────────────────────────────────────────────────
#  Feedback
# ──────────────────────────────────────────────────────────

class Feedback(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='feedbacks'
    )
    rating = models.IntegerField()
    comment = models.TextField()

    def __str__(self):
        return f"Feedback for {self.project.title} ({self.rating}/5)"


# ──────────────────────────────────────────────────────────
#  Task Comment
# ──────────────────────────────────────────────────────────

class TaskComment(models.Model):
    """
    Comments on tasks. Clients can comment on tasks within their projects.
    Admins can comment on any task. Employees on assigned tasks.
    """
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_comments',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"
