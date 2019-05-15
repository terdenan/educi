from django.contrib import admin

from courses.models import Course, CourseCreationRequest, Membership


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    pass


@admin.register(CourseCreationRequest)
class CourseCreationAdmin(admin.ModelAdmin):
    actions = ['approve_requests', 'refuse_requests']

    def approve_requests(self, request, queryset):
        for request in queryset:
            request.status = CourseCreationRequest.APPROVED
            request.save()
            course = Course.objects.create(title=request.title, description=request.description)
            course.add_member(request.user, Membership.TEACHER)

    approve_requests.short_description = "Create courses for selected requests"

    def refuse_requests(self, request, queryset):
        queryset.update(status=CourseCreationRequest.REFUSED)

    refuse_requests.short_description = "Refuse selected requests"
