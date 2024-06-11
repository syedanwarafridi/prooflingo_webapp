from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from project.models import Project
from .models import ProjectTeam
from .serializers import (
    CheckEmailSerializer,
    AddProjectTeamSerializer,
    ProjectTeamMemberSerializer,
    RemoveProjectTeamMemberSerializer,
)
from rest_framework.permissions import IsAuthenticated


# Check User Email Exists
class CheckUserByEmailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = CheckEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"].lower()
            if User.objects.filter(email=email).exists():
                return Response({"exists": True}, status=status.HTTP_200_OK)
            else:
                return Response({"exists": False}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Add Team Member To The Project
class AddProjectTeamAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = AddProjectTeamSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {"Team member added to the project successfully"},
                    status=status.HTTP_201_CREATED,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "User with the provided email does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get Project Team Members
class ProjectTeamMembersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, format=None):
        try:
            project = Project.objects.get(id=project_id)
            project_team_members = ProjectTeam.objects.filter(project=project)

            if not project_team_members.exists():
                return Response(
                    {"error": "No team members found for the given project ID."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = ProjectTeamMemberSerializer(project_team_members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project with the given ID does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Remove Team Member from project
class RemoveProjectTeamMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, format=None):
        serializer = RemoveProjectTeamMemberSerializer(data=request.data)
        if serializer.is_valid():
            project_team_id = serializer.validated_data.get("project_team_id")
            try:
                project_team = ProjectTeam.objects.get(id=project_team_id)
                project_team.delete()
                return Response(
                    {"message": "Project team member removed successfully."},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except ProjectTeam.DoesNotExist:
                return Response(
                    {"error": "Project team member with the given ID does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get User Team Projects
class UserTeamProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        try:
            user_project_teams = ProjectTeam.objects.filter(user=request.user)
            user_projects = [
                project_team.project for project_team in user_project_teams
            ]
            user_projects = list(set(user_projects))
            response_data = []
            for project in user_projects:
                project_data = {
                    "project_id": project.id,
                    "project_name": project.project_name,
                    "status": project.status,
                    "deadline": project.deadline,
                    "created_by": project.created_by,
                    "subject": project.subject,
                }
                response_data.append(project_data)
            response = {
                "message": "Teams project fetch successfully",
                "data": response_data,
            }

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
