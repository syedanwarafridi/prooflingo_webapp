from django.urls import path
from .views import (CreateProjectAPIView, ListProjectsAPIView,
                    DeleteProjectsAPIView, DeleteProjectAPIView,
                    UpdateProjectStatusAPIView, DuplicateProjectAPIView,
                    ProjectDocChatAPIView,  ProjectContentAPIView, ProjectPageAPIView, SmartRefAPIView,
                    AssistantAPIView, CreateBilingualProjectAPIView, ProjectSegmentsAPIView, AutoSaveAPIView,
                    TextTunningAPI, UpdateProjectAPIView)

urlpatterns = [

    # #to create the project------> screen 13
    path('create-project/', CreateProjectAPIView.as_view(), name='create_project_api'),
    path('projects/<int:project_id>/docchat/', ProjectDocChatAPIView.as_view(), name='document-chatbot'),
    path('projects/<int:project_id>/content/', ProjectContentAPIView.as_view(), name='project-content'),
    path('projects/<int:project_id>/page/', ProjectPageAPIView.as_view(), name='project_page'),
    path('smart-ref/', SmartRefAPIView.as_view(), name='smart-ref'),
    path('projects/<int:project_id>/segments/', ProjectSegmentsAPIView.as_view(), name='project-segments'),
    path('projects/<int:project_id>/auto-save/', AutoSaveAPIView.as_view(), name='auto-save'),

    # path('api/lang-and-subject/', LanguageAndSubjectDetection.as_view(), name='lang-and-subject-detection'),

    #to view the projects---->screen 4
    path('view-projects/', ListProjectsAPIView.as_view(), name='view_projects_api'),


    #to delete multiple projects--->screen 5
    path('delete-projects/', DeleteProjectsAPIView.as_view(), name='delete_projects_api'),


    #to delete a single project--->screen 10,11,12
    path('delete-project/<int:pk>/', DeleteProjectAPIView.as_view(), name='delete_single_project_api'),


    #to update the project status as completed
    path('update-status/<int:pk>/', UpdateProjectStatusAPIView.as_view(), name='update-project-status'),


    #to create duplicate project
    path('duplicate/<int:pk>/', DuplicateProjectAPIView.as_view(), name='duplicate-project'),

    #to create the project
    path('create-project/', CreateProjectAPIView.as_view(), name='create_project_api'),
    # path('api/lang-and-subject/', LanguageAndSubjectDetection.as_view(), name='lang-and-subject-detection'),

    #for AI Assistant
    path('assistant/', AssistantAPIView.as_view(), name='assistant-api'),


    #for Bilingual files
    path('bilingual-file-create-project/', CreateBilingualProjectAPIView.as_view(), name='assistant-api'),

    #for text tunning assistant
    path('text-tunning/', TextTunningAPI.as_view(), name='Text Tunning'),

     #to update the project name and status
    path('updateproject/<int:pk>/', UpdateProjectAPIView.as_view(), name='update-project-name-and-status'),

]