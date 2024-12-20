from django import forms

from .constants import AlertDetectionType
from .models import Alert


class ShortLabelChoiceField(forms.ChoiceField):
    """ChoiceField personalized in order to show the short_value as label on DjangoValue"""

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        formatted_choices = [(value, value) for value, _ in choices]
        super().__init__(*args, choices=formatted_choices, **kwargs)


class AlertAdminForm(forms.ModelForm):
    name = ShortLabelChoiceField(choices=AlertDetectionType.choices)

    class Meta:
        model = Alert
        fields = "__all__"
