from django.contrib import admin
from firstapp.models import Scraper, Task

# Register your models here.


admin.site.register(Scraper)
# admin.site.register(Scraper)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # list_display = ('book', 'status', 'borrower', 'due_back', 'id')
    # list_filter = ('status', 'due_back')

    fieldsets = (
        (None, {
            'fields': ('name', 'date')
        }),
        ('IDS', {
            'fields': ('unique_id', 'task_id', 'user')
        }),
    )
