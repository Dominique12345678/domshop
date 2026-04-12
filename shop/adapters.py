from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from shop.models import Role

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social provider data before saving.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Extraire les données de Google
        extra_data = sociallogin.account.extra_data
        firstname = extra_data.get('given_name', '')
        lastname = extra_data.get('family_name', '')
        
        # Mettre à jour les champs personnalisés
        user.firstname = firstname
        user.lastname = lastname
        
        # Assigner le rôle par défaut 'client'
        role_client, created = Role.objects.get_or_create(role_name='client')
        user.role = role_client
        
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Ensure custom fields are saved.
        """
        user = super().save_user(request, sociallogin, form)
        return user
