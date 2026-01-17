from .constants import AlertDetectionType, AlertFilterType, AlertTagValues, UserRiskScoreType
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from .models import Alert, Config, TaskSettings, User
from django_select2.forms import Select2MultipleWidget

class MultiChoiceArrayWidget(forms.SelectMultiple):
    """Widget for user-friendly interface for ArrayField with multiple choices"""

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        elif not isinstance(value, list):
            value = [value]
        return super().render(name, value, attrs, renderer)


class MultiChoiceArrayField(SimpleArrayField):
    """Personalized field for ArrayField that supports multiple choices"""

    def __init__(self, base_field, choices, *args, **kwargs):
        self.widget = MultiChoiceArrayWidget(choices=choices)
        super().__init__(base_field, *args, **kwargs)

    def prepare_value(self, value):
        if value is None:
            return []
        return value


class ShortLabelChoiceField(forms.ChoiceField):
    """ChoiceField personalized in order to show the short_value as label on DjangoValue"""

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        formatted_choices = [("", "---------")] + [(value, value) for value, _ in choices]
        super().__init__(*args, choices=formatted_choices, required=False, **kwargs)


class UserAdminForm(forms.ModelForm):
    risk_score = ShortLabelChoiceField(choices=UserRiskScoreType.choices)

    class Meta:
        model = User
        fields = "__all__"


class AlertAdminForm(forms.ModelForm):
    name = forms.ChoiceField(choices=AlertDetectionType.choices, required=True)
    filter_type = forms.ChoiceField(choices=AlertFilterType.choices, required=True)

    tags = forms.MultipleChoiceField(
        choices=[(tag, tag) for tag, _ in AlertTagValues.choices],
        widget=Select2MultipleWidget,
        required=False,
    )
    class Meta:
        model = Alert
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill tags from the instance
        if self.instance and self.instance.pk:
            self.fields['tags'].initial = self.instance.tags

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save the selected tags into the ArrayField
        instance.tags = self.cleaned_data['tags']
        if commit:
            instance.save()
        return instance


class ConfigAdminForm(forms.ModelForm):
    filtered_alerts_types = MultiChoiceArrayField(
        base_field=forms.CharField(),
        choices=AlertDetectionType.choices,
        required=True,
        help_text="Hold down “Control”, or “Command” on a Mac, to select more than one.",
    )
    risk_score_increment_alerts = MultiChoiceArrayField(
        base_field=forms.CharField(),
        choices=AlertDetectionType.choices,
        required=True,
        help_text="Hold down “Control”, or “Command” on a Mac, to select more than one.",
    )
    alert_minimum_risk_score = ShortLabelChoiceField(choices=UserRiskScoreType.choices)
    threshold_user_risk_alert = ShortLabelChoiceField(choices=UserRiskScoreType.choices)

    class Meta:
        model = Config
        fields = "__all__"

    class Media:
        css = {
            "all": ("css/custom_admin.css",),
        }


class TaskSettingsAdminForm(forms.ModelForm):

    class Meta:
        model = TaskSettings
        fields = "__all__"
