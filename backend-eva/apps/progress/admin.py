"""Progress app admin registration."""

from django.contrib import admin

from apps.progress.models import SpacedRepetitionItem, TopicMastery

admin.site.register(TopicMastery)
admin.site.register(SpacedRepetitionItem)
