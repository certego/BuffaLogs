from django.core.mail import send_mail
from django.conf import settings

def send_alert_email(user_email, alert_message):
    subject = "Login Anomaly Detected"
    message = f"Dear user,\n\nAn unusual login activity was detected:\n\n{alert_message}\n\nStay Safe,\nBuffaLogs"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email]) #1 if sent,0 if not
    
