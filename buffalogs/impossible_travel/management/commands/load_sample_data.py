from django.core.management.base import BaseCommand
import yaml
import random
from impossible_travel.models import User, Login
from datetime import datetime

class Command(BaseCommand):
    help = 'Load sample users and login data from random_data.yaml'

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing user data...")
        User.objects.all().delete()
        Login.objects.all().delete()

        with open("examples/random_data.yaml","r") as info:
            data = yaml.safe_load(info)

        for username in data['user_name'][:10]:
            if username not in ['Not Available','N/A']:
                try:
                    user = User.objects.create(
                        username=username.lower().replace(' ',' '),
                        risk_level = 'low'
                    )

                    for _ in range(3):
                        ip_data = random.choice(data['ip'])
                        Login.objects.create(
                            user=user,
                            timestamp=datetime.now(),
                            country_name=ip_data['country_name'],
                            latitude=ip_data['longitude'],
                            longitude=ip_data['longitude'],
                            ip_address=ip_data['address'],
                            user_agent=random.choice(data['user_agent'])
                        )
                    self.stdout.write(self.style.SUCCESS(f'Created user: {username} with login deta'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating user {username}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Successfully created sample users and login data'))