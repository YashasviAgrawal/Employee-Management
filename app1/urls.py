from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # ── Authentication ──────────────────────────────────────
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # ── Admin: User Management ──────────────────────────────
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),

    # ── Skills Management ───────────────────────────────────
    path('skills/', views.SkillListCreateView.as_view(), name='skill_list'),
    path('skills/<int:pk>/', views.SkillDetailView.as_view(), name='skill_detail'),

    # ── Employee Profile ────────────────────────────────────
    path('employee-profiles/', views.EmployeeProfileListView.as_view(), name='employee_profile_list'),
    path('employee-profiles/<int:pk>/', views.EmployeeProfileDetailView.as_view(), name='employee_profile_detail'),
    path('employee/profile/', views.MyEmployeeProfileView.as_view(), name='my_employee_profile'),

    # ── Client Management (Admin only) ──────────────────────
    path('clients/', views.ClientListCreateView.as_view(), name='client_list'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),

    # ── Projects (Role-scoped) ──────────────────────────────
    path('projects/', views.ProjectListCreateView.as_view(), name='project_list'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:project_id>/tasks/', views.ProjectTasksView.as_view(), name='project_tasks'),
    path('projects/<int:project_id>/employees/', views.ProjectEmployeesView.as_view(), name='project_employees'),

    # ── Project Assignments (Admin assigns employees) ───────
    path('project-assignments/', views.ProjectAssignmentListCreateView.as_view(), name='project_assignment_list'),
    path('project-assignments/<int:pk>/', views.ProjectAssignmentDetailView.as_view(), name='project_assignment_detail'),

    # ── Tasks (Role-scoped, employees can now create/delete) ─
    path('tasks/', views.TaskListCreateView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/unassigned/', views.UnassignedTasksView.as_view(), name='unassigned_tasks'),
    path('tasks/<int:task_id>/self-assign/', views.SelfAssignTaskView.as_view(), name='self_assign_task'),

    # ── Task Status History ─────────────────────────────────
    path('tasks/<int:task_id>/history/', views.TaskStatusHistoryView.as_view(), name='task_status_history'),

    # ── Task Comments (All roles, scoped) ───────────────────
    path('tasks/<int:task_id>/comments/', views.TaskCommentListCreateView.as_view(), name='task_comments'),
    path('comments/<int:pk>/', views.TaskCommentDetailView.as_view(), name='comment_detail'),

    # ── Time Logs (Admin + Employee) ────────────────────────
    path('timelogs/', views.TimeLogListCreateView.as_view(), name='timelog_list'),
    path('timelogs/<int:pk>/', views.TimeLogDetailView.as_view(), name='timelog_detail'),

    # ── Attendance (Sign-in / Sign-out / Away) ──────────────
    path('attendance/sign-in/', views.AttendanceSignInView.as_view(), name='attendance_sign_in'),
    path('attendance/sign-out/', views.AttendanceSignOutView.as_view(), name='attendance_sign_out'),
    path('attendance/away/', views.AttendanceAwayView.as_view(), name='attendance_away'),
    path('attendance/return/', views.AttendanceReturnView.as_view(), name='attendance_return'),
    path('attendance/today/', views.AttendanceTodayView.as_view(), name='attendance_today'),
    path('attendance/history/', views.AttendanceHistoryView.as_view(), name='attendance_history'),
    path('admin/attendance/', views.AdminAttendanceListView.as_view(), name='admin_attendance_list'),
    path('admin/attendance/daily-report/', views.AdminDailyAttendanceReportView.as_view(), name='admin_daily_attendance_report'),
    path('admin/attendance/<int:user_id>/', views.AdminAttendanceDetailView.as_view(), name='admin_attendance_detail'),

    # ── Feedback (Admin only) ───────────────────────────────
    path('feedbacks/', views.FeedbackListCreateView.as_view(), name='feedback_list'),
    path('feedbacks/<int:pk>/', views.FeedbackDetailView.as_view(), name='feedback_detail'),

    # ── Client Task Summary ─────────────────────────────────
    path('client/projects/<int:project_id>/task-summary/', views.ClientTaskSummaryView.as_view(), name='client_task_summary'),

    # ── Day-wise Reports ────────────────────────────────────
    path('reports/tasks/daily/', views.DayWiseTaskReportView.as_view(), name='daily_task_report'),

    # ── Role-specific Dashboards ────────────────────────────
    path('employee/dashboard/', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('client/dashboard/', views.ClientDashboardView.as_view(), name='client_dashboard'),
]
