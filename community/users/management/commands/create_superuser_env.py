"""
Management command: create_superuser_env

Creates a superuser from environment variables. Safe to run multiple times —
it skips creation if the username already exists.

Required env vars:
  DJANGO_SUPERUSER_USERNAME  — the admin username
  DJANGO_SUPERUSER_PASSWORD  — the admin password

Optional env vars:
  DJANGO_SUPERUSER_EMAIL     — the admin email (defaults to empty string)

Usage (Render one-off job or shell):
  python manage.py create_superuser_env
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a superuser from environment variables (idempotent).'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '').strip()
        email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()

        if not username:
            raise CommandError(
                'DJANGO_SUPERUSER_USERNAME environment variable is not set.'
            )
        if not password:
            raise CommandError(
                'DJANGO_SUPERUSER_PASSWORD environment variable is not set.'
            )

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Superuser "{username}" already exists — skipping creation.'
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Superuser "{username}" created successfully.'
            )
        )
