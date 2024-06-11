from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Project
from .serializers import ProjectSerializer, ProjectStatusUpdateSerializer, ProjectCreateSerializer
from django.db import transaction
from .serializers import ProjectSerializer, ProjectCreateSerializer
import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import StreamingHttpResponse
import os
from .docChat import docChat
import json
from .smart_refer import smart_ref
import tempfile
from django.core.files.storage import default_storage
from django.db import transaction
from pathlib import Path
from django.conf import settings
from projectTeams.models import ProjectTeam
from rest_framework.permissions import IsAuthenticated

#----------Handling all the formats of bilingual files----------------------------
from .Bilingual_files import (billingual_sengmentation_trados, billingual_segmentation_xml, 
                          billingual_segmentation_mqxliff, billingual_segmentation_mxliff,
                          billingual_segmentation_sdlppx, billingual_segmentation_xliff)
#----------Assistants-------------------
from .Assistants import (comparison_assistant,
                        extract_text_with_table_tags,
                        embed_tables_in_text, 
                        text_tune_assistant,
                        assistant
                        )
# -----> File Readers <------#
from .file_readers import (extract_text_and_tables_word, 
                           extract_text_and_tables_from_pptx, 
                           process_content, process_docx, process_pptx,
                           extract_text_and_tables_from_pptx_segments,
                           extract_text_and_tables_word_segments)


#--------------------------------------------------APIs-------------------------------------------------------
# -----> Project Creation <-----#
class CreateProjectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        try:
            serializer = ProjectCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                with transaction.atomic():
                    project_instance = serializer.save()
                    
                    # Assign editor role to the user who creates the project
                    ProjectTeam.objects.create(user=request.user, project=project_instance, role='editor')
                    
                    # Create directory with project ID
                    project_directory = Path(settings.MEDIA_ROOT) / 'project_files' / str(project_instance.id)
                    project_directory.mkdir(parents=True, exist_ok=True)
                    
                    # Save source and target files inside the directory
                    if request.FILES.get('source_file'):
                        source_file_name = request.FILES['source_file'].name
                        source_file_path = project_directory / source_file_name
                        default_storage.save(str(source_file_path), request.FILES['source_file'])
                        project_instance.source_file = str(source_file_path.relative_to(settings.MEDIA_ROOT))
                    if request.FILES.get('target_file'):
                        target_file_name = request.FILES['target_file'].name
                        target_file_path = project_directory / target_file_name
                        default_storage.save(str(target_file_path), request.FILES['target_file'])
                        project_instance.target_file = str(target_file_path.relative_to(settings.MEDIA_ROOT))
                    
                    project_instance.save()
                    
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -------> Document Chatbot API <-------#
class ProjectDocChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id, format=None):
        try:
            project = Project.objects.get(pk=project_id)
            
            if project.user != request.user:
                return Response({"error": "You do not have permission to access this project"}, status=status.HTTP_403_FORBIDDEN)
            
            source_file_path = project.source_file.path
            
            user_question = request.data.get('question', '')
            
            if not user_question:
                return Response({"error": "Question cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
            
            response = docChat(source_file_path, user_question)
            
            return Response({"response": response}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --------> Content Extraction from pptx and word files <-------- # 
class ProjectContentAPIView(APIView):
    def get(self, request, project_id, format=None):
        try:
            project = Project.objects.get(pk=project_id)
            
            if project.user != request.user:
                return Response({"error": "You do not have permission to access this project"}, status=status.HTTP_403_FORBIDDEN)
            
            source_file_path = os.path.join(settings.MEDIA_ROOT, project.source_file.name)
            target_file_path = os.path.join(settings.MEDIA_ROOT, project.target_file.name)
            
            if not project.source_file or not project.target_file:
                return Response({"error": "Source or target file not found"}, status=status.HTTP_404_NOT_FOUND)
            
            source_file_ext = os.path.splitext(project.source_file.name)[1].lower()
            target_file_ext = os.path.splitext(project.target_file.name)[1].lower()
            
            response_data = {
                "Source": [],
                "Target": []
            }

            if source_file_ext == '.docx':
                source_data = extract_text_and_tables_word(source_file_path)
            elif source_file_ext == '.pptx':
                source_data = extract_text_and_tables_from_pptx(source_file_path)
            else:
                return Response({"error": "Unsupported source file format"}, status=status.HTTP_400_BAD_REQUEST)

            if target_file_ext == '.docx':
                target_data = extract_text_and_tables_word(target_file_path)
            elif target_file_ext == '.pptx':
                target_data = extract_text_and_tables_from_pptx(target_file_path)
            else:
                return Response({"error": "Unsupported target file format"}, status=status.HTTP_400_BAD_REQUEST)

            for file_type, data in [("Source", source_data), ("Target", target_data)]:
                response_data[file_type] = data
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --------> Segments Extraction from pptx and word files <-------- # 
class ProjectSegmentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, format=None):
        try:
            project = Project.objects.get(pk=project_id)
            
            if project.user != request.user:
                return Response({"error": "You do not have permission to access this project"}, status=status.HTTP_403_FORBIDDEN)
            
            source_file_path = os.path.join(settings.MEDIA_ROOT, project.source_file.name)
            target_file_path = os.path.join(settings.MEDIA_ROOT, project.target_file.name)
            
            if not project.source_file or not project.target_file:
                return Response({"error": "Source or target file not found"}, status=status.HTTP_404_NOT_FOUND)
            
            source_file_ext = os.path.splitext(project.source_file.name)[1].lower()
            target_file_ext = os.path.splitext(project.target_file.name)[1].lower()
            
            response_data = {
                "Source": [],
                "Target": []
            }

            if source_file_ext == '.docx':
                source_data = extract_text_and_tables_word_segments(source_file_path)
            elif source_file_ext == '.pptx':
                source_data = extract_text_and_tables_from_pptx_segments(source_file_path)
            else:
                return Response({"error": "Unsupported source file format"}, status=status.HTTP_400_BAD_REQUEST)

            if target_file_ext == '.docx':
                target_data = extract_text_and_tables_word_segments(target_file_path)
            elif target_file_ext == '.pptx':
                target_data = extract_text_and_tables_from_pptx_segments(target_file_path)
            else:
                return Response({"error": "Unsupported target file format"}, status=status.HTTP_400_BAD_REQUEST)

            for file_type, data in [("Source", source_data), ("Target", target_data)]:
                response_data[file_type] = data
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------> Pagination and History <-------------#
class ProjectPageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id, format=None):
        try:
            project = Project.objects.get(pk=project_id)

            if project.user != request.user:
                return Response({"error": "You do not have permission to access this project"}, status=status.HTTP_403_FORBIDDEN)

            page_no = request.query_params.get('page_no')
            
            if page_no is None:
                return Response({"error": "Page number is required as a query parameter"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                page_no = int(page_no)
            except ValueError:
                return Response({"error": "Page number must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            data = request.data
            subject_matter = project.subject
            language = project.target_language
            history = data.get("Target", [])[:page_no]
            segments = project.segments

            if "Source" not in data or "Target" not in data:
                return Response({"error": "Source and Target keys are required in request data"}, status=status.HTTP_400_BAD_REQUEST)

            source_text, target_text, response = process_content(data["Source"][page_no], data["Target"][page_no], history, subject_matter, language, segments)

            response_data = {
                "translation": json.loads(response),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except KeyError as e:
            return Response({"error": f"Missing key in request data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------> AUTO SAVE API <---------- #
class AutoSaveAPIView(APIView):
    def post(self, request, project_id, format=None):
        try:
            project = Project.objects.get(pk=project_id)

            if project.user != request.user:
                return Response({"error": "You do not have permission to access this project"}, status=status.HTTP_403_FORBIDDEN)

            target_file_path = os.path.join(settings.MEDIA_ROOT, project.target_file.name)
            target_file_ext = os.path.splitext(project.target_file.name)[1].lower()

            if not project.target_file:
                return Response({"error": "Target file not found"}, status=status.HTTP_404_NOT_FOUND)

            comparison_data = request.data
            if not comparison_data:
                return Response({"error": "Comparison data is required"}, status=status.HTTP_400_BAD_REQUEST)

            updated_file_dir = Path(settings.MEDIA_ROOT) / 'updated_target_files' / str(project.id)
            updated_file_dir.mkdir(parents=True, exist_ok=True)
            
            if target_file_ext == '.docx':
                updated_file_path = updated_file_dir / f"updated_target_{project.id}.docx"
                process_docx(updated_file_path, comparison_data)
            elif target_file_ext == '.pptx':
                updated_file_path = updated_file_dir / f"updated_target_{project.id}.pptx"
                process_pptx(updated_file_path, comparison_data)
            else:
                return Response({"error": "Unsupported target file format"}, status=status.HTTP_400_BAD_REQUEST)
            
            project.updated_target_file = str(updated_file_path.relative_to(settings.MEDIA_ROOT))
            project.save()

            return Response({"message": "File updated and saved successfully"}, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#------> Smart Reference <-----#
class SmartRefAPIView(APIView):
    def post(self, request, format=None):
        try:
            file = request.FILES.get('file')
            translation = request.data.get('translation')

            if not file:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

            if not translation:
                return Response({"error": "No translation text provided"}, status=status.HTTP_400_BAD_REQUEST)

            temp_dir = tempfile.mkdtemp()

            temp_file_path = os.path.join(temp_dir, file.name)
            with open(temp_file_path, 'wb+') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            result = smart_ref(temp_file_path, translation)
            
            os.remove(temp_file_path)
            os.rmdir(temp_dir)

            return Response({"result": result}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#API for viewing all projects--->screen 4
class ListProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        # Retrieve projects for the logged-in user
        projects = Project.objects.filter(user=request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
#API to delete multiple projects---->screen 5
class DeleteProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, format=None):
        pks = request.data.get('pks', [])
        if not isinstance(pks, list):
            return Response({"error": "pks must be a list of primary keys"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Retrieve projects that belong to the logged-in user and have primary keys in the list
            projects = Project.objects.filter(pk__in=pks, user=request.user)
            if not projects.exists():
                return Response({"error": "No matching projects found"}, status=status.HTTP_404_NOT_FOUND)
            
            count, _ = projects.delete()
            return Response({"message": f"{count} projects deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#API to delete single project----->screen 10,11,12
class DeleteProjectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, format=None):
        try:
            project = Project.objects.get(pk=pk, user=request.user)
            project.delete()
            return Response({"message": f"Project {pk} deleted"}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({"error": "Project not found or you do not have permission to delete this project"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#API to update project status to completed
class UpdateProjectStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk, format=None):
        try:
            # Ensure the project belongs to the logged-in user
            project = Project.objects.get(pk=pk, user=request.user)
        except Project.DoesNotExist:
            return Response({"error": "Project not found or you do not have permission to update this project"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProjectStatusUpdateSerializer(project, data={'status': 'completed'}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Project status updated to Completed"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#API to Duplicate the Project
class DuplicateProjectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        try:
            # Ensure the project belongs to the logged-in user
            original_project = Project.objects.get(pk=pk, user=request.user)
        except Project.DoesNotExist:
            return Response({"error": "Project not found or you do not have permission to duplicate this project"}, status=status.HTTP_404_NOT_FOUND)
        
        # Duplicate the project
        with transaction.atomic():
            new_project = Project.objects.create(
                user=request.user,
                project_name=self.generate_unique_project_name(original_project.project_name),
                source_file=original_project.source_file,
                target_file=original_project.target_file,
                status=original_project.status,
                deadline=original_project.deadline,
                created_by=original_project.created_by,
                subject=original_project.subject,
                source_language=original_project.source_language,
                target_language=original_project.target_language,
                translation_memory=original_project.translation_memory,
                segments=original_project.segments
            )
        return Response({"message": "Project duplicated successfully"}, status=status.HTTP_201_CREATED)
    
    def generate_unique_project_name(self, original_name):
        copy_count = 1
        new_name = f"{original_name}_copy{copy_count}"
        while Project.objects.filter(project_name=new_name).exists():
            copy_count += 1
            new_name = f"{original_name}_copy{copy_count}"
        return new_name

#AI Assistant API
class AssistantAPIView(APIView):
    def post(self, request, format=None):
        target_text = request.data.get('target_text')
        query = request.data.get('query')
        
        if not target_text or not query:
            return Response({"error": "Both target_text and query are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Call the assistant function
        result = assistant(target_text, query)
        
        return Response({"response": result}, status=status.HTTP_200_OK)
    
#api to create project with bilingual files
class CreateBilingualProjectAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        try:
            bilingual_file = request.FILES.get('bilingual_file')
            if not bilingual_file:
                return Response({"error": "No bilingual file provided"}, status=status.HTTP_400_BAD_REQUEST)

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in bilingual_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Getting other project data from the request
            subject = request.data.get('subject')
            project_name = request.data.get('project_name')
            deadline = request.data.get('deadline')
            source_language = request.data.get('source_language')
            target_language = request.data.get('target_language')
            translation_memory = request.data.get('translation_memory')
            created_by = request.data.get('created_by')

            # Getting the file extension to determine the appropriate function
            file_extension = os.path.splitext(bilingual_file.name)[1].lower()

            # Calling the appropriate segmentation function based on the file extension
            if file_extension in ['.sdlxliff', '.txlf']:
                source_file, target_file = billingual_sengmentation_trados(temp_file_path)
            elif file_extension == '.xml':
                source_file, target_file = billingual_segmentation_xml(temp_file_path)
            elif file_extension == '.mqxliff':
                source_file, target_file = billingual_segmentation_mqxliff(temp_file_path)
            elif file_extension == '.mxliff':
                source_file, target_file = billingual_segmentation_mxliff(temp_file_path)
            elif file_extension == '.sdlppx':
                source_file, target_file = billingual_segmentation_sdlppx(temp_file_path)
            elif file_extension == '.xliff':
                source_file, target_file = billingual_segmentation_xliff(temp_file_path)
            else:
                return Response({"error": "Unsupported file type"}, status=status.HTTP_400_BAD_REQUEST)

            source_file = InMemoryUploadedFile(source_file, None, f'{os.path.basename(bilingual_file.name).split(".")[0]}_source.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', source_file.getbuffer().nbytes, None)
            target_file = InMemoryUploadedFile(target_file, None, f'{os.path.basename(bilingual_file.name).split(".")[0]}_target.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', target_file.getbuffer().nbytes, None)

            project_data = {
                'subject': subject,
                'project_name': project_name,
                'deadline': deadline,
                'source_language': source_language,
                'target_language': target_language,
                'translation_memory': translation_memory,
                'created_by': created_by,
                'source_file': source_file,
                'target_file': target_file
            }

            serializer = ProjectCreateSerializer(data=project_data)

            if serializer.is_valid():
                project = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#-------Text Tunning API-----------------
class TextTunningAPI(APIView):
    def post(self, request):
        word = request.data.get('word')
        word_language= request.data.get('word_language')
        
        if not word:
            return Response({"error": "Word is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        response = text_tune_assistant(word, word_language)
        response = json.loads(response)

        return Response(response)
    
#API to update the name of the project and status of the project
class UpdateProjectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk, format=None):
        data = request.data
        new_name = data.get('new_name', None)
        mark_as_completed = data.get('mark_as_completed', None)
        
        try:
            project = Project.objects.get(pk=pk, user=request.user)
        except Project.DoesNotExist:
            return Response({"error": "Project not found or you do not have permission to update this project"}, status=status.HTTP_404_NOT_FOUND)
        
        if new_name:
            project.project_name = new_name
        
        if mark_as_completed is not None:  
            if mark_as_completed:  
                project.status = 'completed'
        
        project.save()
        
        return Response({"message": "Project updated successfully"}, status=status.HTTP_200_OK)