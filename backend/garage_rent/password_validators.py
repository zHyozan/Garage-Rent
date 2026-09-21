from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PasswordCharacterValidator:
    def validate(self, password, user=None):
        if not any(character.isupper() for character in password):
            raise ValidationError(_("A senha deve conter pelo menos uma letra maiúscula."), code="password_no_uppercase")
        if not any(character.isdigit() for character in password):
            raise ValidationError(_("A senha deve conter pelo menos um número."), code="password_no_digit")
        if not any(not character.isalnum() and not character.isspace() for character in password):
            raise ValidationError(_("A senha deve conter pelo menos um símbolo."), code="password_no_symbol")

    def get_help_text(self):
        return _("A senha deve conter pelo menos uma letra maiúscula, um número e um símbolo.")
