from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ProjectTeam
from project.models import Project

# Check Email Serializer
class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=6, required=True)


# Add Project Team Serializer
class AddProjectTeamSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    project_id = serializers.IntegerField(write_only=True)
    role = serializers.CharField()

    class Meta:
        model = ProjectTeam
        fields = ["email", "project_id", "role"]

    def validate_role(self, value):
        valid_roles = ["editor", "viewer", "commenter"]
        if value.lower() not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of {', '.join(valid_roles)}.")
        return value

    def create(self, validated_data):
        email = validated_data.pop("email").lower()
        project_id = validated_data.pop("project_id")
        role = validated_data.pop("role")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        project = Project.objects.get(id=project_id)
        if ProjectTeam.objects.filter(user=user).exists():
            raise serializers.ValidationError("User is already a member of this project team.")
        project_team = ProjectTeam.objects.create(user=user, project=project, role=role)
        return project_team
    
    
# Project Team Members Serializer
class ProjectTeamMemberSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source='pk')
    user_id = serializers.IntegerField(source='user.id')
    fullname = serializers.CharField(source='user.first_name')
    user_email = serializers.EmailField(source='user.email')
    user_profile_image = serializers.ImageField(source='user.profile.profile_image', read_only=True)

    class Meta:
        model = ProjectTeam
        fields = ['project_id','user_id', 'fullname', 'user_email', 'user_profile_image', 'role']
        
        
# Remove Project Team Members Serializer
class RemoveProjectTeamMemberSerializer(serializers.Serializer):
    project_team_id = serializers.IntegerField()