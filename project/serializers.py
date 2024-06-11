from rest_framework import serializers
from .models import Project
from django.utils import timezone


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields= ['id', 'project_name', 'source_file', 'target_file', 'status', 'deadline' ,'created_by']

class ProjectStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['status']

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ['user']

    def validate_deadline(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("The deadline cannot be in the past.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        project = Project.objects.create(user=user, **validated_data)
        return project
    
# class ProjectCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Project
#         fields = '__all__'