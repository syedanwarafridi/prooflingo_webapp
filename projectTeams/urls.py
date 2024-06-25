from django.urls import path
from .views import (
    CheckUserByEmailAPIView,
    AddProjectTeamAPIView,
    RemoveTeamMemberAPIView,
    AddMemberToTeamAPIView,
    TeamMembersView,
    UserTeamsView,
    SharedProjectsView,
    CreateTeamAPIView,
    ProjectShareMembersView,
    RemoveProjectTeamMemberAPIView
)

urlpatterns = [
    path("check-email/", CheckUserByEmailAPIView.as_view(), name="check-email"),
    path('create-team/', CreateTeamAPIView.as_view(), name='create-team'),
    
    path("add-team-members/", AddMemberToTeamAPIView.as_view(), name="add-team-members"),
    path("share-project-team/", AddProjectTeamAPIView.as_view(), name="share-project-team"),
    
    path("get-user-teams/", UserTeamsView.as_view(), name="get-user-teams"),
    path('team/<int:team_id>/members/', TeamMembersView.as_view(), name='team-members'),
    path('share-project/<int:project_id>/members/', ProjectShareMembersView.as_view(), name='project-share-members'),
    
    path("get-team-shared-projects/<int:team_id>/",SharedProjectsView.as_view(),name="shared-projects"),
    path("remove-team-member/",  RemoveTeamMemberAPIView.as_view(), name="remove-team-member"),
    path("remove-project-team-member/",  RemoveProjectTeamMemberAPIView.as_view(), name="remove-project-team-member"),
]
