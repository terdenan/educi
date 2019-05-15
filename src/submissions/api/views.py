from django.shortcuts import get_object_or_404

from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from courses.models import Course
from courses.api.permissions import IsTeacher, IsTA, IsStudent, IsMember
from submissions.models import Submission
from submissions.api.permissions import IsSender, IsHimself, UpdateSubmissionReviewer
from submissions.api.serializers import SubmissionSerializer, SubmissionUpdateSerializer


class BaseMangerView(views.APIView):
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'VIEWS_BY_METHOD'):
            raise Exception('VIEWS_BY_METHOD static dictionary variable must be defined on a ManageView class!')
        if request.method in self.VIEWS_BY_METHOD:
            return self.VIEWS_BY_METHOD[request.method]()(request, *args, **kwargs)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class SubmissionCreateView(generics.CreateAPIView):
    serializer_class = SubmissionSerializer
    queryset = Submission.objects.all()
    permission_classes = (IsAuthenticated, IsMember)

    def post(self, request, *args, **kwargs):
        course_id = kwargs['pk']
        course = get_object_or_404(Course, pk=course_id)
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            submission = serializer.save(user=request.user)
            serialized_submission = self.serializer_class(submission)

            return Response(serialized_submission.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class SubmissionDetailView(generics.RetrieveAPIView):
    serializer_class = SubmissionSerializer
    lookup_url_kwarg = 'submission_id'
    queryset = Submission.objects.all()
    permission_classes = (IsAuthenticated, IsTeacher | IsTA | IsSender)


class SubmissionListView(generics.ListAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, IsTeacher | IsTA)

    def get_queryset(self):
        course_id = self.kwargs['pk']
        queryset = Submission.objects.filter(assignment__course__id=course_id)
        return queryset

    def get(self, request, *args, **kwargs):
        submissions = self.get_queryset().order_by('user', 'assignment', '-datetime').distinct('user', 'assignment')
        serializer = self.serializer_class(submissions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmissionUpdateView(generics.UpdateAPIView):
    queryset = Submission.objects.all()
    serializer_class = SubmissionUpdateSerializer
    permission_classes = (IsAuthenticated, IsTeacher | IsTA, UpdateSubmissionReviewer)
    lookup_url_kwarg = 'submission_id'


class SubmissionListManageView(BaseMangerView):
    VIEWS_BY_METHOD = {
        'GET': SubmissionListView.as_view,
        'POST': SubmissionCreateView.as_view,
    }


class SubmissionDetailManageView(BaseMangerView):
    VIEWS_BY_METHOD = {
        'GET': SubmissionDetailView.as_view,
        'PATCH': SubmissionUpdateView.as_view,
    }


class UserSubmissionsListView(generics.ListAPIView):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, IsMember, IsHimself)

    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('pk')
        assignment_id = kwargs.get('assignment_id')
        user_id = kwargs.get('user_id')
        submissions = self.queryset.filter(assignment__course__id=course_id, user__id=user_id)
        serializer = self.serializer_class(submissions, many=True)

        return Response(serializer.data, status.HTTP_200_OK)


class UserSubmissionsListManageView(BaseMangerView):
    VIEWS_BY_METHOD = {
        'GET': UserSubmissionsListView.as_view
    }


