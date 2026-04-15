from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.db.models import Count, Q

from .models import (
    Client, Project, Task, TimeLog, Feedback, TaskComment,
    Skill, EmployeeProfile, ProjectAssignment,
    TaskStatusHistory, Attendance, AwayLog,
)
from .permissions import (
    IsAdmin,
    IsEmployee,
    IsClient,
    IsAdminOrReadOnly,
    IsAdminOrEmployee,
    IsTaskAssignee,
    IsTimeLogOwner,
    IsClientProjectOwner,
    IsCommentAuthor,
    IsAttendanceOwner,
    IsProjectAssigned,
)
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    AdminUserSerializer,
    ClientSerializer,
    ProjectSerializer,
    ProjectReadSerializer,
    TaskSerializer,
    TaskClientSerializer,
    EmployeeTaskSerializer,
    TimeLogSerializer,
    EmployeeTimeLogSerializer,
    FeedbackSerializer,
    TaskCommentSerializer,
    SkillSerializer,
    EmployeeProfileSerializer,
    ProjectAssignmentSerializer,
    TaskStatusHistorySerializer,
    AttendanceSerializer,
    AttendanceAdminSerializer,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════════
#  AUTH VIEWS
# ═══════════════════════════════════════════════════════════

class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User registered successfully.',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not user.is_active:
            return Response(
                {'error': 'This account has been deactivated.'},
                status=status.HTTP_403_FORBIDDEN
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful.',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/auth/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logout successful.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/auth/profile/"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


# ═══════════════════════════════════════════════════════════
#  ADMIN-ONLY: USER MANAGEMENT
# ═══════════════════════════════════════════════════════════

class AdminUserListView(generics.ListCreateAPIView):
    """
    GET  /api/admin/users/      — List all users
    POST /api/admin/users/      — Create a new user
    🔒 Admin only
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/admin/users/<id>/
    🔒 Admin only
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]


# ═══════════════════════════════════════════════════════════
#  SKILL MANAGEMENT  (Admin manages, all can read)
# ═══════════════════════════════════════════════════════════

class SkillListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/skills/    — List all skills
    POST /api/skills/    — Create skill (Admin only)
    """
    queryset = Skill.objects.all().order_by('name')
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrReadOnly]


class SkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/skills/<id>/
    🔒 Admin only for writes, read for all authenticated
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrReadOnly]


# ═══════════════════════════════════════════════════════════
#  EMPLOYEE PROFILE MANAGEMENT
# ═══════════════════════════════════════════════════════════

class EmployeeProfileListView(generics.ListAPIView):
    """
    GET /api/employee-profiles/
    Admin: sees all profiles
    Employee: sees own profile only
    """
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAdminOrEmployee]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return EmployeeProfile.objects.all().select_related('user')
        return EmployeeProfile.objects.filter(user=user).select_related('user')


class EmployeeProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT/PATCH /api/employee-profiles/<id>/
    Admin: any profile
    Employee: own profile only
    """
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAdminOrEmployee]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return EmployeeProfile.objects.all().select_related('user')
        return EmployeeProfile.objects.filter(user=user).select_related('user')


class MyEmployeeProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT/PATCH /api/employee/profile/
    Employee can view and update their own profile (skills, etc.)
    """
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsEmployee]

    def get_object(self):
        profile, _ = EmployeeProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile


# ═══════════════════════════════════════════════════════════
#  CLIENT MANAGEMENT  (Admin only)
# ═══════════════════════════════════════════════════════════

class ClientListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/clients/   — List clients
    POST /api/clients/   — Create client
    🔒 Admin only
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdmin]


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/clients/<id>/
    🔒 Admin only
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdmin]


# ═══════════════════════════════════════════════════════════
#  PROJECT VIEWS  (Role-scoped)
# ═══════════════════════════════════════════════════════════

class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/projects/    — List projects (scoped by role)
    POST /api/projects/    — Create project (Admin only)

    Admin:     sees all projects
    Employee:  sees only projects assigned to them (via ProjectAssignment)
    Client:    sees only projects belonging to their client entity
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.role == 'CLIENT':
            return ProjectReadSerializer
        return ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Project.objects.all()
        elif user.role == 'EMPLOYEE':
            # Projects the employee is formally assigned to
            return Project.objects.filter(
                assignments__employee=user
            ).distinct()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if client_profile:
                return Project.objects.filter(client=client_profile)
            return Project.objects.none()
        return Project.objects.none()

    def create(self, request, *args, **kwargs):
        # Only admin can create projects
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can create projects.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/projects/<id>/
    Admin:    full access
    Employee: read-only (assigned projects)
    Client:   read-only (own projects)
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.role == 'CLIENT':
            return ProjectReadSerializer
        return ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Project.objects.all()
        elif user.role == 'EMPLOYEE':
            return Project.objects.filter(
                assignments__employee=user
            ).distinct()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if client_profile:
                return Project.objects.filter(client=client_profile)
            return Project.objects.none()
        return Project.objects.none()

    def update(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can update projects.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can delete projects.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


# ═══════════════════════════════════════════════════════════
#  PROJECT ASSIGNMENT VIEWS  (Admin assigns employees)
# ═══════════════════════════════════════════════════════════

class ProjectAssignmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/project-assignments/           — List assignments
    POST /api/project-assignments/           — Assign employee to project
    🔒 Admin: full access | Employee: read own assignments
    """
    serializer_class = ProjectAssignmentSerializer
    permission_classes = [IsAdminOrEmployee]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return ProjectAssignment.objects.all().select_related(
                'project', 'employee'
            )
        return ProjectAssignment.objects.filter(
            employee=user
        ).select_related('project')

    def create(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can assign employees to projects.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)


class ProjectAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/project-assignments/<id>/
    🔒 Admin only for writes
    """
    serializer_class = ProjectAssignmentSerializer
    permission_classes = [IsAdminOrEmployee]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return ProjectAssignment.objects.all().select_related(
                'project', 'employee'
            )
        return ProjectAssignment.objects.filter(
            employee=user
        ).select_related('project')

    def update(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can modify project assignments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can remove project assignments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class ProjectEmployeesView(generics.ListAPIView):
    """
    GET /api/projects/<project_id>/employees/
    List all employees assigned to a specific project.
    """
    serializer_class = ProjectAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        user = self.request.user

        queryset = ProjectAssignment.objects.filter(
            project_id=project_id
        ).select_related('project', 'employee')

        # Scope by role
        if user.role == 'EMPLOYEE':
            # Only if the employee is assigned to this project
            if not queryset.filter(employee=user).exists():
                return queryset.none()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if not client_profile:
                return queryset.none()
            if not Project.objects.filter(
                id=project_id, client=client_profile
            ).exists():
                return queryset.none()

        return queryset


# ═══════════════════════════════════════════════════════════
#  TASK VIEWS  (Role-scoped — employees can now create/delete)
# ═══════════════════════════════════════════════════════════

class TaskListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/tasks/      — List tasks (scoped)
    POST /api/tasks/      — Create task (Admin or assigned Employee)

    Admin:     sees all tasks, can create for any project
    Employee:  sees tasks assigned to them or in their projects,
               can create tasks in projects they are assigned to
    Client:    sees tasks from their projects only
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return TaskClientSerializer
        if user.role == 'EMPLOYEE':
            return EmployeeTaskSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.select_related(
            'project', 'assigned_to', 'created_by'
        )
        if user.role == 'ADMIN':
            return queryset.all()
        elif user.role == 'EMPLOYEE':
            # Tasks assigned to employee OR tasks in projects assigned to employee
            assigned_projects = ProjectAssignment.objects.filter(
                employee=user
            ).values_list('project_id', flat=True)
            return queryset.filter(
                Q(assigned_to=user) | Q(project_id__in=assigned_projects)
            ).distinct()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if client_profile:
                return queryset.filter(project__client=client_profile)
            return queryset.none()
        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role == 'CLIENT':
            return Response(
                {'error': 'Clients cannot create tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        # For employees, verify they are assigned to the project
        if user.role == 'EMPLOYEE':
            project_id = request.data.get('project')
            if not project_id:
                return Response(
                    {'error': 'Project ID is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not ProjectAssignment.objects.filter(
                project_id=project_id, employee=user
            ).exists():
                return Response(
                    {'error': 'You are not assigned to this project.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/tasks/<id>/
    Admin:    full CRUD
    Employee: full CRUD on tasks in their assigned projects
    Client:   read-only (own project tasks)
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return TaskClientSerializer
        if user.role == 'EMPLOYEE':
            return EmployeeTaskSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.select_related(
            'project', 'assigned_to', 'created_by'
        )
        if user.role == 'ADMIN':
            return queryset.all()
        elif user.role == 'EMPLOYEE':
            assigned_projects = ProjectAssignment.objects.filter(
                employee=user
            ).values_list('project_id', flat=True)
            return queryset.filter(
                Q(assigned_to=user) | Q(project_id__in=assigned_projects)
            ).distinct()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if client_profile:
                return queryset.filter(project__client=client_profile)
            return queryset.none()
        return queryset.none()

    def update(self, request, *args, **kwargs):
        if request.user.role == 'CLIENT':
            return Response(
                {'error': 'Clients cannot update tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Track status change for audit
        instance = self.get_object()
        old_status = instance.status
        response = super().update(request, *args, **kwargs)
        instance.refresh_from_db()
        if instance.status != old_status:
            TaskStatusHistory.objects.create(
                task=instance,
                changed_by=request.user,
                old_status=old_status,
                new_status=instance.status,
            )
        return response

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if user.role == 'CLIENT':
            return Response(
                {'error': 'Clients cannot delete tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Admin can delete any, employee can delete tasks in their projects
        if user.role == 'EMPLOYEE':
            task = self.get_object()
            if not ProjectAssignment.objects.filter(
                project=task.project, employee=user
            ).exists():
                return Response(
                    {'error': 'You can only delete tasks in your assigned projects.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().destroy(request, *args, **kwargs)


# ═══════════════════════════════════════════════════════════
#  TASK SELF-ASSIGNMENT (Employee picks unassigned tasks)
# ═══════════════════════════════════════════════════════════

class UnassignedTasksView(generics.ListAPIView):
    """
    GET /api/tasks/unassigned/
    List unassigned tasks in projects the employee is assigned to.
    Supports ?project=<id> and ?skill=<skill_id> filters.
    """
    serializer_class = EmployeeTaskSerializer
    permission_classes = [IsAdminOrEmployee]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(
            assigned_to__isnull=True
        ).select_related('project')

        if user.role == 'EMPLOYEE':
            assigned_projects = ProjectAssignment.objects.filter(
                employee=user
            ).values_list('project_id', flat=True)
            queryset = queryset.filter(project_id__in=assigned_projects)

        # Optional filters
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        skill_id = self.request.query_params.get('skill')
        if skill_id:
            queryset = queryset.filter(required_skills__id=skill_id)

        return queryset.distinct()


class SelfAssignTaskView(APIView):
    """
    POST /api/tasks/<task_id>/self-assign/
    Employee assigns an unassigned task to themselves.
    """
    permission_classes = [IsEmployee]

    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if task.assigned_to is not None:
            return Response(
                {'error': 'This task is already assigned to someone.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check employee is assigned to the project
        if not ProjectAssignment.objects.filter(
            project=task.project, employee=request.user
        ).exists():
            return Response(
                {'error': 'You are not assigned to this project.'},
                status=status.HTTP_403_FORBIDDEN
            )

        task.assigned_to = request.user
        task.save()
        return Response({
            'message': f'Task "{task.title}" has been assigned to you.',
            'task': EmployeeTaskSerializer(task).data,
        })


# ═══════════════════════════════════════════════════════════
#  TASK FILTER VIEWS  (Convenience for Client)
# ═══════════════════════════════════════════════════════════

class ProjectTasksView(generics.ListAPIView):
    """
    GET /api/projects/<project_id>/tasks/
    List tasks for a specific project. Supports ?status= filter.
    Access is scoped by role (same rules as TaskListCreateView).
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return TaskClientSerializer
        if user.role == 'EMPLOYEE':
            return EmployeeTaskSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs['project_id']
        queryset = Task.objects.filter(
            project_id=project_id
        ).select_related('project', 'assigned_to')

        # Role-based scoping
        if user.role == 'EMPLOYEE':
            assigned_projects = ProjectAssignment.objects.filter(
                employee=user
            ).values_list('project_id', flat=True)
            if int(project_id) not in list(assigned_projects):
                return queryset.none()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if client_profile:
                queryset = queryset.filter(project__client=client_profile)
            else:
                return queryset.none()

        # Optional status filter: ?status=COMPLETED
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        return queryset


class ClientTaskSummaryView(APIView):
    """
    GET /api/client/projects/<project_id>/task-summary/
    Returns counts of running, completed, and upcoming tasks.
    🔒 Client only (or Admin)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        user = request.user

        # Verify access
        if user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if not client_profile:
                return Response(
                    {'error': 'No client profile linked.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not Project.objects.filter(
                id=project_id, client=client_profile
            ).exists():
                return Response(
                    {'error': 'You do not have access to this project.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif user.role != 'ADMIN':
            return Response(
                {'error': 'Access denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()
        tasks = Task.objects.filter(project_id=project_id)

        running_tasks = tasks.filter(status='IN_PROGRESS')
        completed_tasks = tasks.filter(status='COMPLETED')
        upcoming_tasks = tasks.filter(status='TODO', due_date__gte=today)
        overdue_tasks = tasks.filter(due_date__lt=today).exclude(
            status='COMPLETED'
        )
        on_hold_tasks = tasks.filter(status='ON_HOLD')

        return Response({
            'project_id': project_id,
            'running': {
                'count': running_tasks.count(),
                'tasks': TaskClientSerializer(running_tasks, many=True).data,
            },
            'completed': {
                'count': completed_tasks.count(),
                'tasks': TaskClientSerializer(completed_tasks, many=True).data,
            },
            'upcoming': {
                'count': upcoming_tasks.count(),
                'tasks': TaskClientSerializer(upcoming_tasks, many=True).data,
            },
            'overdue': {
                'count': overdue_tasks.count(),
                'tasks': TaskClientSerializer(overdue_tasks, many=True).data,
            },
            'on_hold': {
                'count': on_hold_tasks.count(),
                'tasks': TaskClientSerializer(on_hold_tasks, many=True).data,
            },
        })


# ═══════════════════════════════════════════════════════════
#  TASK STATUS HISTORY (Day-wise audit trail)
# ═══════════════════════════════════════════════════════════

class TaskStatusHistoryView(generics.ListAPIView):
    """
    GET /api/tasks/<task_id>/history/
    View the status change history for a task.
    Scoped by role.
    """
    serializer_class = TaskStatusHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        task_id = self.kwargs['task_id']
        queryset = TaskStatusHistory.objects.filter(
            task_id=task_id
        ).select_related('changed_by')

        # Verify access to the task
        try:
            task = Task.objects.select_related('project__client').get(
                id=task_id
            )
        except Task.DoesNotExist:
            return queryset.none()

        if user.role == 'EMPLOYEE':
            if not ProjectAssignment.objects.filter(
                project=task.project, employee=user
            ).exists() and task.assigned_to != user:
                return queryset.none()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if not client_profile or task.project.client != client_profile:
                return queryset.none()

        return queryset


class DayWiseTaskReportView(APIView):
    """
    GET /api/reports/tasks/daily/
    Get task activity grouped by date.
    Supports ?date=YYYY-MM-DD, ?project=<id>, ?days=7 filters.
    🔒 Admin or assigned Employee
    """
    permission_classes = [IsAdminOrEmployee]

    def get(self, request):
        from datetime import timedelta

        user = request.user
        days = int(request.query_params.get('days', 7))
        specific_date = request.query_params.get('date')
        project_id = request.query_params.get('project')

        queryset = TaskStatusHistory.objects.select_related(
            'task', 'task__project', 'changed_by'
        )

        if user.role == 'EMPLOYEE':
            assigned_projects = ProjectAssignment.objects.filter(
                employee=user
            ).values_list('project_id', flat=True)
            queryset = queryset.filter(
                Q(task__assigned_to=user) |
                Q(task__project_id__in=assigned_projects)
            )

        if project_id:
            queryset = queryset.filter(task__project_id=project_id)

        if specific_date:
            queryset = queryset.filter(changed_at__date=specific_date)
        else:
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(changed_at__gte=start_date)

        # Group by date
        result = {}
        for entry in queryset.order_by('-changed_at'):
            date_str = entry.changed_at.strftime('%Y-%m-%d')
            if date_str not in result:
                result[date_str] = []
            result[date_str].append({
                'task_id': entry.task.id,
                'task_title': entry.task.title,
                'project_title': entry.task.project.title,
                'old_status': entry.old_status,
                'new_status': entry.new_status,
                'changed_by': entry.changed_by.get_full_name() if entry.changed_by else None,
                'changed_at': entry.changed_at.isoformat(),
                'notes': entry.notes,
            })

        return Response(result)


# ═══════════════════════════════════════════════════════════
#  TIMELOG VIEWS  (Admin + Employee)
# ═══════════════════════════════════════════════════════════

class TimeLogListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/timelogs/     — List time logs
    POST /api/timelogs/     — Create time log

    Admin:    sees all, can create for anyone
    Employee: sees only their own, auto-sets user=self
    Client:   no access
    """
    permission_classes = [IsAdminOrEmployee]

    def get_serializer_class(self):
        if self.request.user.role == 'EMPLOYEE':
            return EmployeeTimeLogSerializer
        return TimeLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return TimeLog.objects.all().select_related('user', 'task')
        return TimeLog.objects.filter(user=user).select_related('task')

    def perform_create(self, serializer):
        if self.request.user.role == 'EMPLOYEE':
            serializer.save(user=self.request.user, start_time=timezone.now())
        else:
            serializer.save()


class TimeLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/timelogs/<id>/
    Admin:    full access
    Employee: own time logs only
    Client:   no access
    """
    permission_classes = [IsAdminOrEmployee, IsTimeLogOwner]

    def get_serializer_class(self):
        if self.request.user.role == 'EMPLOYEE':
            return EmployeeTimeLogSerializer
        return TimeLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return TimeLog.objects.all().select_related('user', 'task')
        return TimeLog.objects.filter(user=user).select_related('task')

    def perform_update(self, serializer):
        if self.request.user.role == 'EMPLOYEE':
            serializer.save(end_time=timezone.now())
        else:
            serializer.save()


# ═══════════════════════════════════════════════════════════
#  ATTENDANCE VIEWS  (Sign-in / Sign-out / Away)
# ═══════════════════════════════════════════════════════════

class AttendanceSignInView(APIView):
    """
    POST /api/attendance/sign-in/
    Employee signs in for the day.
    🔒 Employee only
    """
    permission_classes = [IsEmployee]

    def post(self, request):
        user = request.user
        today = timezone.now().date()

        # Check if already signed in today
        existing = Attendance.objects.filter(user=user, date=today).first()
        if existing:
            return Response(
                {
                    'error': 'You are already signed in today.',
                    'attendance': AttendanceSerializer(existing).data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance = Attendance.objects.create(
            user=user,
            date=today,
            sign_in_time=timezone.now(),
            status='SIGNED_IN',
        )
        return Response({
            'message': 'Signed in successfully.',
            'attendance': AttendanceSerializer(attendance).data,
        }, status=status.HTTP_201_CREATED)


class AttendanceSignOutView(APIView):
    """
    POST /api/attendance/sign-out/
    Employee signs out for the day.
    🔒 Employee only
    """
    permission_classes = [IsEmployee]

    def post(self, request):
        user = request.user
        today = timezone.now().date()

        attendance = Attendance.objects.filter(
            user=user, date=today
        ).first()

        if not attendance:
            return Response(
                {'error': 'You have not signed in today.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.status == 'SIGNED_OUT':
            return Response(
                {'error': 'You have already signed out today.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Close any open away logs
        open_away = attendance.away_logs.filter(away_end__isnull=True).first()
        if open_away:
            open_away.away_end = timezone.now()
            open_away.save()

        attendance.sign_out_time = timezone.now()
        attendance.status = 'SIGNED_OUT'
        attendance.save()

        return Response({
            'message': 'Signed out successfully.',
            'attendance': AttendanceSerializer(attendance).data,
        })


class AttendanceAwayView(APIView):
    """
    POST /api/attendance/away/
    Employee marks as away (going out temporarily).
    🔒 Employee only
    """
    permission_classes = [IsEmployee]

    def post(self, request):
        user = request.user
        today = timezone.now().date()

        attendance = Attendance.objects.filter(
            user=user, date=today
        ).first()

        if not attendance:
            return Response(
                {'error': 'You have not signed in today.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.status == 'SIGNED_OUT':
            return Response(
                {'error': 'You have already signed out today.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.status == 'AWAY':
            return Response(
                {'error': 'You are already marked as away.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create away log
        AwayLog.objects.create(
            attendance=attendance,
            away_start=timezone.now(),
        )
        attendance.status = 'AWAY'
        attendance.save()

        return Response({
            'message': 'Marked as away.',
            'attendance': AttendanceSerializer(attendance).data,
        })


class AttendanceReturnView(APIView):
    """
    POST /api/attendance/return/
    Employee returns from away.
    🔒 Employee only
    """
    permission_classes = [IsEmployee]

    def post(self, request):
        user = request.user
        today = timezone.now().date()

        attendance = Attendance.objects.filter(
            user=user, date=today
        ).first()

        if not attendance:
            return Response(
                {'error': 'You have not signed in today.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.status != 'AWAY':
            return Response(
                {'error': 'You are not currently marked as away.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Close the open away log
        open_away = attendance.away_logs.filter(
            away_end__isnull=True
        ).first()
        if open_away:
            open_away.away_end = timezone.now()
            open_away.save()

        attendance.status = 'SIGNED_IN'
        attendance.save()

        return Response({
            'message': 'Welcome back! Marked as returned.',
            'attendance': AttendanceSerializer(attendance).data,
        })


class AttendanceTodayView(APIView):
    """
    GET /api/attendance/today/
    Get today's attendance status for the logged-in employee.
    🔒 Employee only
    """
    permission_classes = [IsEmployee]

    def get(self, request):
        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            user=request.user, date=today
        ).prefetch_related('away_logs').first()

        if not attendance:
            return Response({
                'message': 'You have not signed in today.',
                'attendance': None,
            })

        return Response({
            'attendance': AttendanceSerializer(attendance).data,
        })


class AttendanceHistoryView(generics.ListAPIView):
    """
    GET /api/attendance/history/
    Get attendance history for the logged-in employee.
    Supports ?start_date= and ?end_date= filters.
    🔒 Employee only
    """
    serializer_class = AttendanceSerializer
    permission_classes = [IsEmployee]

    def get_queryset(self):
        queryset = Attendance.objects.filter(
            user=self.request.user
        ).prefetch_related('away_logs')

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset


class AdminAttendanceListView(generics.ListAPIView):
    """
    GET /api/admin/attendance/
    Admin can view all employee attendance records.
    Supports ?date=, ?user=, ?status= filters.
    🔒 Admin only
    """
    serializer_class = AttendanceAdminSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = Attendance.objects.all().select_related(
            'user'
        ).prefetch_related('away_logs')

        date_filter = self.request.query_params.get('date')
        user_filter = self.request.query_params.get('user')
        status_filter = self.request.query_params.get('status')

        if date_filter:
            queryset = queryset.filter(date=date_filter)
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        return queryset


class AdminAttendanceDetailView(generics.ListAPIView):
    """
    GET /api/admin/attendance/<user_id>/
    Admin views a specific employee's attendance history.
    🔒 Admin only
    """
    serializer_class = AttendanceAdminSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        queryset = Attendance.objects.filter(
            user_id=user_id
        ).prefetch_related('away_logs')

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset


class AdminDailyAttendanceReportView(APIView):
    """
    GET /api/admin/attendance/daily-report/
    Admin sees total present, total absent, and names of employees for a specific date.
    Supports ?date=YYYY-MM-DD
    🔒 Admin only
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            date_filter = timezone.now().date()
        else:
            from datetime import datetime
            try:
                date_filter = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        
        all_employees = User.objects.filter(role='EMPLOYEE', is_active=True)
        attendances = Attendance.objects.filter(date=date_filter).select_related('user')
        
        present_users_set = {a.user for a in attendances}
        
        present_list = [{
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'status': next((a.status for a in attendances if a.user == u), 'UNKNOWN')
        } for u in present_users_set]
        
        absent_users = set(all_employees) - present_users_set
        
        absent_list = [{
            'id': u.id, 
            'name': u.get_full_name() or u.username
        } for u in absent_users]
        
        return Response({
            'date': date_filter,
            'present_count': len(present_list),
            'present_employees': present_list,
            'absent_count': len(absent_list),
            'absent_employees': absent_list
        })


# ═══════════════════════════════════════════════════════════
#  FEEDBACK VIEWS  (Admin only)
# ═══════════════════════════════════════════════════════════

class FeedbackListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/feedbacks/    — List feedback
    POST /api/feedbacks/    — Create feedback
    🔒 Admin only
    """
    queryset = Feedback.objects.all().select_related('project')
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdmin]


class FeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/feedbacks/<id>/
    🔒 Admin only
    """
    queryset = Feedback.objects.all().select_related('project')
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdmin]


# ═══════════════════════════════════════════════════════════
#  TASK COMMENT VIEWS  (All roles, scoped)
# ═══════════════════════════════════════════════════════════

class TaskCommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/tasks/<task_id>/comments/   — List comments on a task
    POST /api/tasks/<task_id>/comments/   — Add a comment

    Admin:    all tasks
    Employee: assigned tasks only
    Client:   own project tasks only
    """
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        task_id = self.kwargs['task_id']
        queryset = TaskComment.objects.filter(
            task_id=task_id
        ).select_related('author')

        # Verify the user has access to this task
        try:
            task = Task.objects.select_related('project__client').get(
                id=task_id
            )
        except Task.DoesNotExist:
            return queryset.none()

        if user.role == 'EMPLOYEE' and task.assigned_to != user:
            # Also check project assignment
            if not ProjectAssignment.objects.filter(
                project=task.project, employee=user
            ).exists():
                return queryset.none()
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if not client_profile or task.project.client != client_profile:
                return queryset.none()

        return queryset

    def perform_create(self, serializer):
        task_id = self.kwargs['task_id']
        task = Task.objects.select_related('project__client').get(id=task_id)

        # Verify access before creating
        user = self.request.user
        if user.role == 'EMPLOYEE' and task.assigned_to != user:
            if not ProjectAssignment.objects.filter(
                project=task.project, employee=user
            ).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    "You can only comment on tasks in your assigned projects."
                )
        elif user.role == 'CLIENT':
            client_profile = getattr(user, 'client_profile', None)
            if not client_profile or task.project.client != client_profile:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    "You can only comment on tasks in your projects."
                )

        serializer.save(author=self.request.user, task=task)


class TaskCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/comments/<id>/
    Only the author can update/delete (Admin bypasses).
    """
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]
    queryset = TaskComment.objects.all().select_related('author', 'task')


# ═══════════════════════════════════════════════════════════
#  DASHBOARD / REPORT VIEWS
# ═══════════════════════════════════════════════════════════

class AdminDashboardView(APIView):
    """
    GET /api/admin/dashboard/
    Summary statistics for the admin dashboard.
    🔒 Admin only
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        total_users = User.objects.count()
        users_by_role = dict(
            User.objects.values_list('role').annotate(count=Count('id'))
            .values_list('role', 'count')
        )

        total_projects = Project.objects.count()
        total_tasks = Task.objects.count()
        tasks_by_status = dict(
            Task.objects.values_list('status').annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        total_time_logs = TimeLog.objects.count()
        total_assignments = ProjectAssignment.objects.count()

        # Today's attendance summary
        today = timezone.now().date()
        today_attendance = Attendance.objects.filter(date=today)
        attendance_summary = {
            'total_signed_in': today_attendance.filter(
                status='SIGNED_IN'
            ).count(),
            'total_away': today_attendance.filter(status='AWAY').count(),
            'total_signed_out': today_attendance.filter(
                status='SIGNED_OUT'
            ).count(),
        }

        return Response({
            'total_users': total_users,
            'users_by_role': users_by_role,
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'tasks_by_status': tasks_by_status,
            'total_time_logs': total_time_logs,
            'total_project_assignments': total_assignments,
            'today_attendance': attendance_summary,
        })


class EmployeeDashboardView(APIView):
    """
    GET /api/employee/dashboard/
    Summary for the logged-in employee.
    🔒 Employee only
    """
    permission_classes = [IsEmployee]

    def get(self, request):
        user = request.user

        assigned_tasks = Task.objects.filter(assigned_to=user)
        tasks_by_status = dict(
            assigned_tasks.values_list('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        total_time_logs = TimeLog.objects.filter(user=user).count()

        # Projects via assignment
        assignments = ProjectAssignment.objects.filter(
            employee=user
        ).select_related('project')
        my_projects = [
            {
                'id': a.project.id,
                'title': a.project.title,
                'role': a.role_in_project,
            }
            for a in assignments
        ]

        # Today's attendance
        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            user=user, date=today
        ).first()
        attendance_data = None
        if attendance:
            attendance_data = AttendanceSerializer(attendance).data

        return Response({
            'total_assigned_tasks': assigned_tasks.count(),
            'tasks_by_status': tasks_by_status,
            'total_time_logs': total_time_logs,
            'my_projects': my_projects,
            'today_attendance': attendance_data,
        })


class ClientDashboardView(APIView):
    """
    GET /api/client/dashboard/
    Summary for the logged-in client.
    🔒 Client only
    """
    permission_classes = [IsClient]

    def get(self, request):
        client_profile = getattr(request.user, 'client_profile', None)
        if not client_profile:
            return Response(
                {'error': 'No client profile linked to this account.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        projects = Project.objects.filter(client=client_profile)
        tasks = Task.objects.filter(project__client=client_profile)
        tasks_by_status = dict(
            tasks.values_list('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        today = timezone.now().date()

        return Response({
            'company_name': client_profile.company_name,
            'total_projects': projects.count(),
            'total_tasks': tasks.count(),
            'tasks_by_status': tasks_by_status,
            'running_tasks': tasks.filter(status='IN_PROGRESS').count(),
            'completed_tasks': tasks.filter(status='COMPLETED').count(),
            'upcoming_tasks': tasks.filter(
                status='TODO', due_date__gte=today
            ).count(),
        })
