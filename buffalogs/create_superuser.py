import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "buffalogs.settings.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    username = 'admin'
    email = 'admin@buffalogs.local'
    password = 'buffalogs2024!'

    try:
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            print(f'Superuser {username} created successfully')
        else:
            print(f'Superuser {username} already exists')
    except Exception as e:
        print(f'Error creating superuser: {e}')

if __name__ == '__main__':
    create_superuser()