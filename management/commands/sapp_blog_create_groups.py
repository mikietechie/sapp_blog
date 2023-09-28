from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group


class Command(BaseCommand):
    help = 'Create SAPP Blog Group'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="Blog Users")
        group.permissions.set(Permission.objects.filter(content_type__app_label="sapp_blog"))
        self.stdout.write(self.style.SUCCESS(f"Todo Users Group Created successfully!"))
