from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    PROJECT_STATUS_CHOICES = [
        ('inprogress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    project_name = models.CharField(max_length=255)
    source_file = models.FileField(upload_to='source_files/')
    target_file = models.FileField(upload_to='target_files/')
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default='inprogress')
    deadline = models.DateField()
    created_by = models.CharField(max_length=100)
    # source_text = models.TextField(blank=True)
    # target_text = models.TextField(blank=True)
    subject = models.CharField(max_length=100, default=None)
    source_language = models.CharField(max_length=50)
    target_language = models.CharField(max_length=50)
    translation_memory = models.BooleanField(default=False)
    segments = models.BooleanField(default=False)
    
    def __str__(self):
        return self.project_name