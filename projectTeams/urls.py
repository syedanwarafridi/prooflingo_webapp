from django.urls import path
from .views import (
    CheckUserByEmailAPIView,
    AddProjectTeamAPIView,
    ProjectTeamMembersAPIView,
    UserTeamProjectsAPIView,
    RemoveProjectTeamMemberAPIView
)

urlpatterns = [
    path('check-email/', CheckUserByEmailAPIView.as_view(), name='check-email'),
    
    path('add-project-team/', AddProjectTeamAPIView.as_view(), name='add-project-team'),
    path('project/<int:project_id>/team-members/', ProjectTeamMembersAPIView.as_view(), name='project-team-members'),
    path('remove-project-team-member/', RemoveProjectTeamMemberAPIView.as_view(), name='remove-project-team-member'),
    path('user-team-projects/', UserTeamProjectsAPIView.as_view(), name='user-team-projects'),

]