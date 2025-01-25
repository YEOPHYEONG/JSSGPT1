from django.contrib import admin
from .models import RawExperience, STARExperience

class STARExperienceInline(admin.TabularInline):
    model = STARExperience
    extra = 0  # 추가 항목 없이 표시
    fields = ('title', 'situation', 'task', 'action', 'result', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')  # 읽기 전용 필드

@admin.register(RawExperience)
class RawExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'resume_file', 'created_at', 'updated_at')
    inlines = [STARExperienceInline]  # Star Experience를 인라인으로 포함
    from django.contrib import admin

from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from django.template.response import TemplateResponse
from .models import STARExperience

@admin.register(STARExperience)
class STARExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'situation', 'task', 'action', 'result', 'created_at', 'updated_at', 'view_grouped_link')
    search_fields = ('title', 'situation', 'task', 'action', 'result')

    # 유저 그룹화된 페이지로 이동하는 링크 추가
    def view_grouped_link(self, obj):
        return format_html(
            '<a href="{}">View Grouped</a>',
            '/admin/user_experience/starexperience/grouped/'
        )
    view_grouped_link.short_description = "Grouped View"

    # 커스텀 URL 추가
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('grouped/', self.grouped_view, name="grouped_star_experiences"),
        ]
        return custom_urls + urls

    # 그룹화된 뷰
    def grouped_view(self, request):
        # 유저별로 Star Experience를 그룹화
        users = STARExperience.objects.values('user__username').distinct()
        grouped_data = {
            user['user__username']: STARExperience.objects.filter(user__username=user['user__username'])
            for user in users
        }
        return TemplateResponse(
            request,
            "admin/grouped_star_experiences.html",
            {'grouped_data': grouped_data}
        )