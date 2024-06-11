from django.db import models
from django.contrib.auth.models import User
from project.models import Project


class ProjectTeam(models.Model):
    ROLE_CHOICES = [
        ("editor", "Editor"),
        ("viewer", "Viewer"),
        ("contributor", "Contributor"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, choices=ROLE_CHOICES)

    def __str__(self):
        return self.project.project_name
