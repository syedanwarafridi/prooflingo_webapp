from rest_framework import permissions

class IsCommentAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the requesting user is the author of the comment
        return obj.author == request.user
