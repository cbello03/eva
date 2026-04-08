"""Projects app admin registration."""

from django.contrib import admin

from apps.projects.models import (
    PeerReviewAssignment,
    Project,
    ProjectReview,
    ProjectSubmission,
    SubmissionFile,
)

admin.site.register(Project)
admin.site.register(ProjectSubmission)
admin.site.register(SubmissionFile)
admin.site.register(ProjectReview)
admin.site.register(PeerReviewAssignment)
