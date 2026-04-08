"""Management command to seed default users for local development."""

from django.core.management.base import BaseCommand

from apps.accounts.models import Role, User

SEED_USERS = [
    {
        "email": "student@eva.local",
        "username": "student",
        "display_name": "Demo Student",
        "password": "student123",
        "role": Role.STUDENT,
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "email": "teacher@eva.local",
        "username": "teacher",
        "display_name": "Demo Teacher",
        "password": "teacher123",
        "role": Role.TEACHER,
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "email": "admin@eva.local",
        "username": "admin",
        "display_name": "Demo Admin",
        "password": "admin123",
        "role": Role.ADMIN,
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "email": "superadmin@eva.local",
        "username": "superadmin",
        "display_name": "Super Admin",
        "password": "superadmin123",
        "role": Role.ADMIN,
        "is_superuser": True,
        "is_staff": True,
    },
]


class Command(BaseCommand):
    help = "Create default demo users (student, teacher, admin, superadmin) for local development."

    def handle(self, *args, **options):
        for data in SEED_USERS:
            email = data["email"]
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  ⏭  {email} already exists, skipping.")
                continue

            user = User(
                email=email,
                username=data["username"],
                display_name=data["display_name"],
                role=data["role"],
                is_superuser=data["is_superuser"],
                is_staff=data["is_staff"],
            )
            user.set_password(data["password"])
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  ✔  Created {data['role']} → {email}"))

        self.stdout.write(self.style.SUCCESS("\nDone. Seed users ready."))
