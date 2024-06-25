from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.contrib.auth.models import User
from project.models import Project
from .models import *
from .serializers import (
    CheckEmailSerializer,
    AddProjectTeamSerializer,
    RemoveTeamMemberSerializer,
    AddMembersToTeamSerializer,
    TeamMemberSerializer,
    ProjectSerializer,
    CreateTeamSerializer,
    RemoveProjectTeamMemberSerializer
)
from rest_framework.permissions import IsAuthenticated
from accounts.models import UserProfile
from django.shortcuts import get_object_or_404


# Check User Email Exists
class CheckUserByEmailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = CheckEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"].lower()
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    if user_profile.profile_image:
                        profile_image_url = request.build_absolute_uri(
                            user_profile.profile_image.url
                        )
                    else:
                        profile_image_url = None
                except UserProfile.DoesNotExist:
                    profile_image_url = None
                response = {
                    "message": "User found against email address",
                    "data": [
                        {
                            "user_id": user.id,
                            "full_name": user.first_name,
                            "email": user.email,
                            "profile_image": profile_image_url,
                        }
                    ],
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = {
                    "message": "No user found against email address",
                    "data": [],
                }
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
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
                    {"message": "Project shared with team member successfully"},
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


# Remove Team Member From Team
class RemoveTeamMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, format=None):
        serializer = RemoveTeamMemberSerializer(data=request.data)
        if serializer.is_valid():
            team_id = serializer.validated_data.get("team_id")
            user_id = serializer.validated_data.get("user_id")
            team_member = TeamMember.objects.get(team__id=team_id, user__id=user_id)
            team_member.delete()
            return Response(
                {"message": "User removed from team successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        errors = serializer.errors
        response = {}
        if 'non_field_errors' in errors:
            response['error'] = errors['non_field_errors'][0]
        else:
            response['error'] = "Invalid data provided."
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Remove Team Member From Project
class RemoveProjectTeamMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, format=None):
        serializer = RemoveProjectTeamMemberSerializer(data=request.data)
        if serializer.is_valid():
            team_id = serializer.validated_data.get("team_id")
            project_id = serializer.validated_data.get("project_id")
            user_id = serializer.validated_data.get("user_id")
            team_member = TeamMember.objects.get(team__id=team_id, user__id=user_id)
            project_team = ProjectTeam.objects.get(project__id=project_id, team_member=team_member)
            project_team.delete()
            return Response(
                {"message": "User removed from project successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        errors = serializer.errors
        response = {}
        if 'non_field_errors' in errors:
            response['error'] = errors['non_field_errors'][0]
        else:
            response['error'] = "Invalid data provided."
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

# Add New Team Member
class AddMemberToTeamAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddMembersToTeamSerializer(data=request.data)
        if serializer.is_valid():
            errors = []
            successes = []

            for member_data in serializer.validated_data["members"]:
                email = member_data["email"].lower()
                team_id = member_data["team_id"]

                try:
                    team = Team.objects.get(id=team_id)
                except Team.DoesNotExist:
                    errors.append(
                        {
                            "email": email,
                            "message": "Team against given id does not exist.",
                        }
                    )
                    continue

                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    errors.append(
                        {
                            "email": email,
                            "message": "User with the provided email does not exist.",
                        }
                    )
                    continue

                if TeamMember.objects.filter(user=user, team=team).exists():
                    errors.append(
                        {"email": email, "message": "User is already in the team."}
                    )
                else:
                    TeamMember.objects.create(user=user, team=team)
                    successes.append(
                        {
                            "email": email,
                            "message": "Member added to team successfully.",
                        }
                    )

            response = {"successes": successes, "errors": errors}
            return Response(response, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get User Teams
class UserTeamsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        team_members = TeamMember.objects.filter(user=user)
        serializer = TeamMemberSerializer(team_members, many=True)
        response = {
            "message": "Teams fetched successfully",
            "data": serializer.data,
        }
        return Response(response, status=status.HTTP_200_OK)


# Get Team Share Project
class SharedProjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        # Get the team instance
        team = get_object_or_404(Team, id=team_id)

        # Ensure the current user is a member of the team
        if not TeamMember.objects.filter(team=team, user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this team."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project_teams = ProjectTeam.objects.filter(team_member__team=team)
        projects = Project.objects.filter(
            id__in=project_teams.values_list("project_id", flat=True)
        )
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


# Get Team Members
class TeamMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        # Get the team instance
        team = get_object_or_404(Team, id=team_id)

        # Ensure the current user is a member of the team
        if not TeamMember.objects.filter(team=team, user=request.user).exists():
            return Response({"error": "You are not a member of this team."}, status=403)

        # Get all members of the team
        team_members = TeamMember.objects.filter(team=team)

        team_members_data = []
        for member in team_members:
            try:
                user_profile = UserProfile.objects.get(user=member.user)
                if user_profile.profile_image:
                    profile_image_url = request.build_absolute_uri(
                        user_profile.profile_image.url
                    )
                else:
                    profile_image_url = None
            except UserProfile.DoesNotExist:
                profile_image_url = None
            member_data = {
                "team_id": member.team.id,
                "user_id": member.user.id,
                "full_name": member.user.first_name,
                "email": member.user.email,
                "profile_image": profile_image_url,
                # Add more fields as necessary
            }
            team_members_data.append(member_data)

        return Response(team_members_data)


# Create Team
class CreateTeamAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = CreateTeamSerializer(data=request.data)
        if serializer.is_valid():
            try:
                team = serializer.save()
                response = {
                    "message": "Team created successfully",
                    "data": {
                        "id": team.id,
                        "name": team.name,
                        "owner": team.owner.id,
                    },
                }
                return Response(response, status=status.HTTP_201_CREATED)
            except User.DoesNotExist:
                return Response(
                    {"error": "User with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            errors = serializer.errors
            response = {}
            if 'non_field_errors' in errors:
                response['error'] =  errors['non_field_errors'][0]
            else:
                response['error'] = serializer.errors
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Get Project share Members
class ProjectShareMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            
            project = get_object_or_404(Project, id=project_id)
        except Project.DoesNotExist:
                return Response(
                    {"error": "Project with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        project_members = ProjectTeam.objects.filter(project=project)

        project_members_data = []
        for member in project_members:
            try:
                user_profile = UserProfile.objects.get(user=member.team_member.user)
                if user_profile.profile_image:
                    profile_image_url = request.build_absolute_uri(
                        user_profile.profile_image.url
                    )
                else:
                    profile_image_url = None
            except UserProfile.DoesNotExist:
                profile_image_url = None
            member_data = {
                "team_id": member.team_member.team.id,
                "project_id": member.project.id,
                "user_id": member.team_member.user.id,
                "full_name": member.team_member.user.first_name,
                "email": member.team_member.user.email,
                "profile_image": profile_image_url,
                "role":member.role
            }
            project_members_data.append(member_data)

        return Response(project_members_data)