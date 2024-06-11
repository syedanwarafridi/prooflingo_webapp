from django.urls import path
from .views import (
    AddProjectCommentAPIView,
    GetProjectCommentsAPIView,
    UpdateCommentAPIView,
    AddCommentReplyAPIView,
    UpdateReplyAPIView,
    DeleteCommentAPIView,
    DeleteCommentReplyAPIView,
)

urlpatterns = [
    #Comments API
    path('add-project-comment/', AddProjectCommentAPIView.as_view(), name='add-project-comment'),
    path('update-project-comment/<int:pk>/', UpdateCommentAPIView.as_view(), name='update-project-comment'),
    path('project/<int:project_id>/comments/', GetProjectCommentsAPIView.as_view(), name='project-comments-list'),
    path('delete-project-comment/<int:comment_id>/', DeleteCommentAPIView.as_view(), name='delete-project-comment'),
    
    # Replies API
    path('add-project-comment-reply/', AddCommentReplyAPIView.as_view(), name='add-project-comment-reply'),
    path('update-project-comment-reply/<int:pk>/', UpdateReplyAPIView.as_view(), name='update=project-comment-reply'),
    path('delete-project-comment-reply/<int:reply_id>/', DeleteCommentReplyAPIView.as_view(), name='delete-project-comment-reply'),
  
]
