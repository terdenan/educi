from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from courses.models import Assignment
from courses.api.permissions import IsCourseStaff
from build_rules.api.serializers import RuleSerializer
from build_rules.models import Rule


class RuleListCreateAPIView(generics.ListCreateAPIView):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = (IsAuthenticated, IsCourseStaff)

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        assignment_id = self.kwargs['assignment_id']
        queryset = queryset.\
            filter(assignment__course__id=course_id, assignment__id=assignment_id).\
            order_by('order')
        return queryset

    def create(self, request, pk=None, assignment_id=None):
        # FIXME
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        serializer = self.serializer_class(data=request.data, context={
            'assignment': assignment
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RuleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = (IsAuthenticated, IsCourseStaff)
    lookup_url_kwarg = 'rule_id'

    def filter_queryset(self, queryset):
        course_id = self.kwargs['pk']
        assignment_id = self.kwargs['assignment_id']
        queryset = queryset.\
            filter(assignment__course__id=course_id, assignment__id=assignment_id)
        return queryset


@api_view(['POST'])
@permission_classes((IsAuthenticated, IsCourseStaff))
def move(request, pk, assignment_id, rule_id):
    obj = Rule.objects.get(
        pk=rule_id, assignment__id=assignment_id, assignment__course__id=pk,
    )
    new_order = request.data.get('order', None)

    if new_order is None:
        return Response(
            data={'error': 'No order given'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if int(new_order) < 1:
        return Response(
            data={'error': 'Order cannot be zero or below'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    Rule.objects.move(obj, new_order)
    return Response({'success': True, 'order': new_order})
