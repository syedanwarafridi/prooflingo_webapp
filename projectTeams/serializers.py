from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from project.models import Project


# Check Email Serializer
class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=6, required=True)


# Add Project Team Serializer
class AddProjectTeamSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    project_id = serializers.IntegerField(write_only=True)
    team_id = serializers.IntegerField(write_only=True)
    role = serializers.CharField()

    class Meta:
        model = ProjectTeam
        fields = ["email", "project_id", "role", "team_id"]

    def validate_role(self, value):
        valid_roles = ["editor", "viewer", "commenter"]
        if value.lower() not in valid_roles:
            raise serializers.ValidationError(
                f"Role must be one of {', '.join(valid_roles)}."
            )
        return value

    def create(self, validated_data):
        email = validated_data.pop("email").lower()
        project_id = validated_data.pop("project_id")
        role = validated_data.pop("role")
        team_id = validated_data.pop("team_id")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            raise serializers.ValidationError("Team against id does not exist.")
        project = Project.objects.get(id=project_id)
        try:
            team_member = TeamMember.objects.get(team=team, user=user)
        except TeamMember.DoesNotExist:
            raise serializers.ValidationError("User is not a team member.")
        if ProjectTeam.objects.filter(
            team_member=team_member, project=project
        ).exists():
            raise serializers.ValidationError("Project already share with team member.")
        project_team = ProjectTeam.objects.create(
            project=project, role=role, team_member=team_member
        )
        return project_team


# Remove Team Members Serializer
class RemoveTeamMemberSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    
    def validate(self, data):
        user_id = data.get("user_id")
        team_id = data.get("team_id")
        try:
            TeamMember.objects.get(team__id=team_id, user__id=user_id)
        except TeamMember.DoesNotExist:
            raise serializers.ValidationError("User is not a member of this Team")
        return data


# Remove Project Team Members Serializer
class RemoveProjectTeamMemberSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    project_id = serializers.IntegerField()
    user_id = serializers.IntegerField()

    def validate(self, data):
        user_id = data.get("user_id")
        team_id = data.get("team_id")
        project_id = data.get("project_id")
        try:
            team_member = TeamMember.objects.get(team__id=team_id, user__id=user_id)
        except TeamMember.DoesNotExist:
            raise serializers.ValidationError("User is not a member of this Team")
        try:
            ProjectTeam.objects.get(project__id=project_id, team_member=team_member)
        except ProjectTeam.DoesNotExist:
            raise serializers.ValidationError("Project with this ID does not exist.")
        return data


# Add Bulk Team Members Serializer
class MemberEntrySerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=6, required=True)
    team_id = serializers.IntegerField()


class AddMembersToTeamSerializer(serializers.Serializer):
    members = serializers.ListField(child=MemberEntrySerializer())


# Team Serializer
class TeamSerializer(serializers.ModelSerializer):
    team_id = serializers.IntegerField(source="id")
    team_name = serializers.CharField(source="name")
    team_owner_id = serializers.IntegerField(source="owner.id")

    class Meta:
        model = Team
        fields = ["team_id", "team_name", "team_owner_id"]


# Team Member Serializer
class TeamMemberSerializer(serializers.ModelSerializer):
    team = TeamSerializer()

    class Meta:
        model = TeamMember
        fields = ["team"]


# Share Project Serializer
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


# Create Team
class CreateTeamSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    user_id = serializers.IntegerField()

    def validate(self, data):
        name = data.get("name")
        user_id = data.get("user_id")

        # Check if the user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "User with the provided ID does not exist."
            )

        # Check if a team with the same name already exists for this user
        if Team.objects.filter(name=name, owner=user).exists():
            raise serializers.ValidationError(
                "A team with this name already exists for this user."
            )

        return data

    def create(self, validated_data):
        name = validated_data.get("name")
        user_id = validated_data.get("user_id")
        user = User.objects.get(id=user_id)
        team = Team.objects.create(name=name, owner=user)
        TeamMember.objects.create(team=team, user=user)
        return team
