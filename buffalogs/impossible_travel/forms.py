from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from .constants import AlertDetectionType
from .models import Alert, Config


class MultiChoiceArrayWidget(forms.SelectMultiple):
    """Widget per ArrayField che consente selezioni multiple con un'interfaccia user-friendly."""

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices


class MultiChoiceArrayField(SimpleArrayField):
    """Campo personalizzato per ArrayField con supporto a choices multiple."""

    def __init__(self, base_field, choices, *args, **kwargs):
        self.widget = MultiChoiceArrayWidget(choices=choices)
        super().__init__(base_field, *args, **kwargs)


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


class ConfigAdminForm(forms.ModelForm):
    filtered_alerts_types = MultiChoiceArrayField(
        base_field=forms.CharField(),
        choices=AlertDetectionType.choices,
        required=False,
        help_text="Hold down “Control”, or “Command” on a Mac, to select more than one.",
    )

    class Meta:
        model = Config
        fields = "__all__"
