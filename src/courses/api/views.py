from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError

from courses.api.serializers import CourseSerializer, CourseMembersSerializer, AssignmentSerializer,\
    EnvironmentSerializer, CourseCreationRequestSerializer
from courses.models import Course, Assignment, Membership, Environment, CourseCreationRequest
from courses.api.permissions import IsTeacher, IsTA, IsStudent, IsMember, IsCourseStaff, IsRequester
from courses.utils.attachments import list_attachments, upload_attachments

User = get_user_model()


class BaseManageView(views.APIView):
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'VIEWS_BY_METHOD'):
            raise Exception('VIEWS_BY_METHOD static dictionary variable must be defined on a ManageView class!')
        if request.method in self.VIEWS_BY_METHOD:
            return self.VIEWS_BY_METHOD[request.method]()(request, *args, **kwargs)

        return Response(status=405)


class CourseCreateView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)


class CourseUpdateView(generics.UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsTeacher)


class CourseDeleteView(generics.DestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)


class CourseListManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': CourseListView.as_view,
        'POST': CourseCreateView.as_view,
    }


class CourseDetailManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': CourseDetailView.as_view,
        'DELETE': CourseDeleteView.as_view,
        'PUT': CourseUpdateView.as_view,
    }


class CourseCreationRequestCreateView(views.APIView):
    queryset = CourseCreationRequest.objects.all()
    serializer_class = CourseCreationRequestSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={
            'user': request.user
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseCreationRequestListView(generics.ListAPIView):
    queryset = CourseCreationRequest.objects.all()
    serializer_class = CourseCreationRequestSerializer
    permission_classes = (IsAuthenticated,)

    def filter_queryset(self, queryset):
        user = self.request.user
        queryset = queryset.filter(user=user)
        return queryset


class CourseCreationRequestListManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': CourseCreationRequestListView.as_view,
        'POST': CourseCreationRequestCreateView.as_view,
    }


class CourseMembersCreateView(views.APIView):
    queryset = Membership.objects.all()
    serializer_class = CourseMembersSerializer
    permission_classes = (IsAuthenticated, IsTeacher | IsTA)

    def post(self, request, **kwargs):
        course_id = kwargs['pk']
        course = get_object_or_404(Course, pk=course_id)

        serializer = self.serializer_class(data=request.data, context={
            'course': course
        })
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except ObjectDoesNotExist:
            return Response({'email': ['User with specified email was\'t found']},
                            status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'email': ['User with specified email has been already enrolled']},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseMembersListView(generics.ListAPIView):
    queryset = Membership.objects.all()
    serializer_class = CourseMembersSerializer
    permission_classes = (IsAuthenticated, IsCourseStaff)

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        queryset = queryset.\
            filter(course__id=course_id)
        return queryset


class CourseMembersRetrieveDestroyAPIView(generics.RetrieveDestroyAPIView):
    queryset = Membership.objects.all()
    serializer_class = CourseMembersSerializer
    permission_classes = (IsAuthenticated, IsTeacher | IsTA | IsRequester)
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        queryset = queryset.\
            filter(course__id=course_id)
        return queryset


class CourseMembersListManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': CourseMembersListView.as_view,
        'POST': CourseMembersCreateView.as_view,
    }


class CourseAssignmentCreateView(views.APIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = (IsAuthenticated, IsTeacher)

    def post(self, request, **kwargs):
        course_id = kwargs['pk']
        course = get_object_or_404(Course, pk=course_id)

        serializer = self.serializer_class(data=request.data, context={
            'course': course
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseAssignmentListView(generics.ListAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = (IsAuthenticated, IsMember)

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        queryset = queryset.\
            filter(course__id=course_id)
        return queryset


class CourseAssignmentDetailView(generics.RetrieveAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = (IsAuthenticated, IsMember)
    lookup_url_kwarg = 'assignment_id'

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        queryset = queryset.\
            filter(course__id=course_id)
        return queryset


class CourseAssignmentUpdateView(generics.UpdateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = (IsAuthenticated, IsTeacher)
    lookup_url_kwarg = 'assignment_id'

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        queryset = queryset.\
            filter(course__id=course_id)
        return queryset


class CourseAssignmentDeleteView(generics.DestroyAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = (IsAuthenticated, IsTeacher)
    lookup_url_kwarg = 'assignment_id'

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        queryset = queryset.\
            filter(course__id=course_id)
        return queryset


class CourseAssignmentListManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': CourseAssignmentListView.as_view,
        'POST': CourseAssignmentCreateView.as_view,
    }


class CourseAssignmentDetailManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': CourseAssignmentDetailView.as_view,
        'PUT': CourseAssignmentUpdateView.as_view,
        'PATCH': CourseAssignmentUpdateView.as_view,
        'DELETE': CourseAssignmentDeleteView.as_view,
    }


class EnvironmentCreateView(views.APIView):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = (IsAuthenticated, IsTeacher)

    def post(self, request, **kwargs):
        course_id = kwargs['pk']
        course = get_object_or_404(Course, pk=course_id)

        serializer = self.serializer_class(data=request.data, context={
            'course': course
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EnvironmentListView(generics.ListAPIView):
    serializer_class = EnvironmentSerializer
    permission_classes = (IsAuthenticated, IsTeacher | IsTA)

    def get_queryset(self):
        course_id = self.kwargs['pk']
        queryset = Environment.objects.filter(course__id=course_id)
        return queryset


class EnvironmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EnvironmentSerializer
    queryset = Environment.objects.all()
    permission_classes = (IsAuthenticated, IsCourseStaff)
    lookup_url_kwarg = 'environment_id'

    def get_queryset(self):
        course_id = self.kwargs['pk']
        queryset = Environment.objects.filter(course__id=course_id)
        return queryset


class EnvironmentListManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': EnvironmentListView.as_view,
        'POST': EnvironmentCreateView.as_view,
    }


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated, IsTeacher))
def manage_attachments(request, pk):
    if request.method == 'POST':
        attachments = request.FILES.getlist('attachments', [])
        upload_attachments(pk, attachments)

    attachments = list_attachments(pk)
    return Response({'attachments': attachments})
