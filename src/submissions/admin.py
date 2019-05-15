from django.contrib import admin

from submissions.models import Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    pass
