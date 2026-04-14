import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Mocking settings if not already configured
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_project.settings')
    django.setup()

def test_email_sending():
    print("--- Testing Email Sending (Console Backend) ---")
    try:
        send_mail(
            "Test Confirm Code",
            "Votre code est : 123456",
            "from@domshop.com",
            ["target@example.com"],
            fail_silently=False,
        )
        print("\n--- Test Finished ---")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_email_sending()
