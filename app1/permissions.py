from rest_framework.permissions import BasePermission, SAFE_METHODS


# ──────────────────────────────────────────────────────────
#  Base role permissions
# ──────────────────────────────────────────────────────────

class IsAdmin(BasePermission):
    """Allows access only to users with role=ADMIN."""
    message = "Admin access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsEmployee(BasePermission):
    """Allows access only to users with role=EMPLOYEE."""
    message = "Employee access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'EMPLOYEE'
        )


class IsClient(BasePermission):
    """Allows access only to users with role=CLIENT."""
    message = "Client access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'CLIENT'
        )


# ──────────────────────────────────────────────────────────
#  Composite permissions
# ──────────────────────────────────────────────────────────

class IsAdminOrReadOnly(BasePermission):
    """
    Admin gets full access; others get read-only.
    Useful for resources where everyone can view but only admin can modify.
    """
    message = "Only admins can modify this resource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == 'ADMIN'


class IsAdminOrEmployee(BasePermission):
    """Allows access to Admin or Employee users."""
    message = "Admin or Employee access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('ADMIN', 'EMPLOYEE')
        )


# ──────────────────────────────────────────────────────────
#  Object-level permissions
# ──────────────────────────────────────────────────────────

class IsTaskAssignee(BasePermission):
    """
    Object-level: employee can only access tasks assigned to them.
    Admin bypasses this check.
    """
    message = "You can only access tasks assigned to you."

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        return obj.assigned_to == request.user


class IsTimeLogOwner(BasePermission):
    """
    Object-level: employee can only access their own time logs.
    Admin bypasses this check.
    """
    message = "You can only access your own time logs."

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        return obj.user == request.user


class IsClientProjectOwner(BasePermission):
    """
    Object-level: client users can only access projects belonging to
    their linked Client entity.  Admin bypasses.
    """
    message = "You can only access your own projects."

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        if request.user.role == 'CLIENT':
            client_profile = getattr(request.user, 'client_profile', None)
            if client_profile is None:
                return False
            # obj might be a Project or a Task/Comment under a project
            if hasattr(obj, 'client'):
                return obj.client == client_profile
            if hasattr(obj, 'project'):
                return obj.project.client == client_profile
        return False


class IsCommentAuthor(BasePermission):
    """
    Object-level: only the author can update/delete their comment.
    Admin bypasses.
    """
    message = "You can only modify your own comments."

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAttendanceOwner(BasePermission):
    """
    Object-level: employee can only access their own attendance records.
    Admin bypasses.
    """
    message = "You can only access your own attendance records."

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        return obj.user == request.user


class IsProjectAssigned(BasePermission):
    """
    Checks whether an employee is assigned to the project.
    Used for employee task creation — employee can only create tasks
    in projects they are assigned to.
    Admin bypasses.
    """
    message = "You are not assigned to this project."

    def has_permission(self, request, view):
        from .models import ProjectAssignment
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'ADMIN':
            return True
        if request.method in SAFE_METHODS:
            return True
        # For writes, check project assignment
        project_id = request.data.get('project')
        if project_id:
            return ProjectAssignment.objects.filter(
                project_id=project_id, employee=request.user
            ).exists()
        return True
