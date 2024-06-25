from django.db import models
from django.contrib.auth.models import User
from project.models import Project

class Team(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, related_name='owner', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    user = models.ForeignKey(User, related_name='team_member', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='team', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'team')
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        return f"{self.user.first_name} ({self.team.name})"

class ProjectTeam(models.Model):
    ROLE_CHOICES = [
        ("editor", "Editor"),
        ("viewer", "Viewer"),
        ("contributor", "Contributor"),
    ]
    team_member = models.ForeignKey(TeamMember, related_name='team_member', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name='project', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ('team_member', 'project')
        verbose_name = 'Project Team Role'
        verbose_name_plural = 'Project Team Roles'

    def __str__(self):
        return f"{self.project.project_name} - {self.team_member.user.first_name} ({self.role})"
