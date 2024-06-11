from rest_framework.permissions import IsAuthenticated
from .models import Comments, Replies
from .serializers import (
    AddCommentSerializer,
    ProjectCommentsSerializer,
    CommentSerializer,
    AddCommentReplySerializer,
    ReplySerializer,
    RepliesSerializer
)
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import User
from project.models import Project
from .permissions import IsCommentAuthor


# Add Comment To The Project
class AddProjectCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = AddCommentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                comment = serializer.save()
                response = {
                    "message": "Comment added to the project successfully",
                    "data": ProjectCommentsSerializer(comment).data,
                }
                return Response(
                    response,
                    status=status.HTTP_201_CREATED,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "User with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get Project Comments
class GetProjectCommentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, format=None):
        try:
            project = Project.objects.get(id=project_id)
            project_comments = Comments.objects.filter(project=project)

            if not project_comments.exists():
                return Response([],status=status.HTTP_200_OK)
            serializer = ProjectCommentsSerializer(project_comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project with the given ID does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Edit Comment Details
class UpdateCommentAPIView(generics.UpdateAPIView):
    queryset = Comments.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


# Add Comment To The Project
class AddCommentReplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = AddCommentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {"Comment added to the project successfully"},
                    status=status.HTTP_201_CREATED,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "User with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Add Reply To The Comment
class AddCommentReplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = AddCommentReplySerializer(data=request.data)
        if serializer.is_valid():
            try:
                reply = serializer.save()
                response = {
                    "message": "Comment added to the project successfully",
                    "data": RepliesSerializer(reply).data,
                }
                return Response(
                    response,
                    status=status.HTTP_201_CREATED,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "User with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Comments.DoesNotExist:
                return Response(
                    {"error": "Comment with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Edit Replies Details
class UpdateReplyAPIView(generics.UpdateAPIView):
    queryset = Replies.objects.all()
    serializer_class = ReplySerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


# Delete Comment Details
class DeleteCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id, format=None):
        try:
            comment = Comments.objects.get(id=comment_id, author=request.user)
            comment.delete()
            return Response(
                {"message": "Comment deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Comments.DoesNotExist:
            return Response(
                {
                    "error": "Comment not found or you do not have permission to delete this comment."
                },
                status=status.HTTP_404_NOT_FOUND,
            )


# Delete Comment Replies Details
class DeleteCommentReplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, reply_id, format=None):
        try:
            reply = Replies.objects.get(id=reply_id, author=request.user)
            reply.delete()
            return Response(
                {"message": "Reply deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Replies.DoesNotExist:
            return Response(
                {
                    "error": "Reply not found or you do not have permission to delete this comment."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
