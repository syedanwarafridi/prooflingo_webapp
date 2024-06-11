from rest_framework import serializers
from django.contrib.auth.models import User
from project.models import Project
from projectTeams.models import ProjectTeam
from .models import Comments, Replies


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ["id", "project", "author", "comment", "created_at"]
        read_only_fields = ["id", "project", "author", "created_at"]


class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Replies
        fields = ["id", "comment", "author", "reply", "created_at"]
        read_only_fields = ["id", "comment", "author", "created_at"]


# Add Project Comment Serializer
class AddCommentSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True)
    comment = serializers.CharField()

    class Meta:
        model = Comments
        fields = ["user_id", "project_id", "comment"]

    def validate(self, data):
        user_id = data.get("user_id")
        project_id = data.get("project_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist.")
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project with this ID does not exist.")
        if not ProjectTeam.objects.filter(user=user, project=project).exists():
            raise serializers.ValidationError(
                "User is not a member of this project team."
            )
        return data

    def create(self, validated_data):
        user = User.objects.get(id=validated_data["user_id"])
        project = Project.objects.get(id=validated_data["project_id"])
        comment = validated_data["comment"]

        project_comment = Comments.objects.create(
            author=user, project=project, comment=comment
        )
        return project_comment


# Replies Serializer
class RepliesSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="author.id")
    fullname = serializers.CharField(source="author.get_full_name")
    user_email = serializers.EmailField(source="author.email")
    user_profile_image = serializers.ImageField(
        source="author.profile.profile_image", read_only=True
    )

    class Meta:
        model = Replies
        fields = [
            "id",
            "user_id",
            "fullname",
            "user_email",
            "user_profile_image",
            "reply",
            "created_at",
        ]


# Get Project Comments Serializer
class ProjectCommentsSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source="project.id")
    user_id = serializers.IntegerField(source="author.id")
    fullname = serializers.CharField(source="author.get_full_name")
    user_email = serializers.EmailField(source="author.email")
    user_profile_image = serializers.ImageField(
        source="author.profile.profile_image", read_only=True
    )
    replies = RepliesSerializer(many=True, read_only=True)

    class Meta:
        model = Comments
        fields = [
            "id",
            "project_id",
            "user_id",
            "fullname",
            "user_email",
            "user_profile_image",
            "comment",
            "created_at",
            "replies",
        ]


# Add Comment Reply Serializer
class AddCommentReplySerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(write_only=True)
    project_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True)
    reply = serializers.CharField()

    class Meta:
        model = Comments
        fields = ["user_id", "project_id", "comment_id", "reply"]

    def validate(self, data):
        user_id = data.get("user_id")
        comment_id = data.get("comment_id")
        project_id = data.get("project_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist.")
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project with this ID does not exist.")
        try:
            Comments.objects.get(id=comment_id)
        except Comments.DoesNotExist:
            raise serializers.ValidationError("Comment with this ID does not exist.")
        if not ProjectTeam.objects.filter(user=user, project=project).exists():
            raise serializers.ValidationError(
                "User is not a member of this project team."
            )
        return data

    def create(self, validated_data):
        user = User.objects.get(id=validated_data["user_id"])
        comment = Comments.objects.get(id=validated_data["comment_id"])
        reply = validated_data["reply"]

        comment_reply = Replies.objects.create(
            author=user, reply=reply, comment=comment
        )
        return comment_reply
