from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Wallet

User = settings.AUTH_USER_MODEL  # Custom User

from django.apps import apps

UserModel = apps.get_model(*User.split('.'))

@receiver(post_save, sender = UserModel)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Signal to automatically create a Wallet when a new User is created.
    """
    if created:
        Wallet.objects.get_or_create(user = instance)