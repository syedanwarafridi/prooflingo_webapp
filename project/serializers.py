from rest_framework import serializers
from .models import Project
from django.utils import timezone


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields= ['id', 'project_name', 'source_file', 'target_file', 'status', 'deadline' ,'created_by', 'source_language', 'target_language', 'bilingual']

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

###############################################
class BilingoProjectCreateSerializer(serializers.ModelSerializer):
    bilingual_file = serializers.FileField(write_only=True)

    class Meta:
        model = Project
        fields = ['id', 'project_name', 'bilingual_file', 'status', 'deadline', 'subject', 'source_language', 'target_language', 'bilingual', 'created_by']
        read_only_fields = ['id', 'status']

    def validate_deadline(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("The deadline cannot be in the past.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        
        bilingual_file = validated_data.pop('bilingual_file', None)
        project = Project.objects.create(user=user, **validated_data)
        project.created_by = str(user.first_name) + " " + str(user.last_name)
        if bilingual_file:
            project.source_file = bilingual_file
            project.target_file = bilingual_file
        
        project.save()
        return project
