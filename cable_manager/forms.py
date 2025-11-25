from django import forms
from .models import CableLine, PDDMeasurementSession, SinglePDMeasurement, HighVoltageTest, Accident, MuffChangeLog

class CableLineForm(forms.ModelForm):
    class Meta:
        model = CableLine
        fields = [
            'number', 'cable_brand', 'start_muff', 'end_muff',
            'connect_muff_1', 'connect_muff_2', 'connect_muff_3',
            'length', 'core_count', 'commissioning_date'
        ]
        widgets = {
            'commissioning_date': forms.DateInput(attrs={'type': 'date'}),
            'connect_muff_1': forms.TextInput(attrs={'placeholder': 'Отсутствует'}),
            'connect_muff_2': forms.TextInput(attrs={'placeholder': 'Отсутствует'}),
            'connect_muff_3': forms.TextInput(attrs={'placeholder': 'Отсутствует'}),
        }

class PDDMeasurementSessionForm(forms.ModelForm):
    class Meta:
        model = PDDMeasurementSession
        fields = ['cable_line', 'session_date', 'notes']
        widgets = {
            'session_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SinglePDMeasurementForm(forms.ModelForm):
    class Meta:
        model = SinglePDMeasurement
        fields = ['voltage_level', 'core_1_discharge', 'core_1_distance',
                 'core_2_discharge', 'core_2_distance', 'core_3_discharge', 'core_3_distance']

class HighVoltageTestForm(forms.ModelForm):
    class Meta:
        model = HighVoltageTest
        fields = ['cable_line', 'test_date', 'test_voltage', 'insulation_resistance']
        widgets = {
            'test_date': forms.DateInput(attrs={'type': 'date'}),
        }

class AccidentForm(forms.ModelForm):
    class Meta:
        model = Accident
        fields = ['cable_line', 'accident_date', 'accident_type', 'description', 'downtime']
        widgets = {
            'accident_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'downtime': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'}),
        }

class MuffChangeLogForm(forms.ModelForm):
    class Meta:
        model = MuffChangeLog
        fields = ['cable_line', 'changed_muff_type', 'old_value', 'new_value', 'notes']

from django.forms import inlineformset_factory

# Добавь в конец файла forms.py

# Formset для нескольких измерений в одной сессии
PDMeasurementFormSet = inlineformset_factory(
    PDDMeasurementSession,
    SinglePDMeasurement,
    form=SinglePDMeasurementForm,
    extra=3,  # Количество пустых форм для добавления
    can_delete=True,
    fields=['voltage_level', 'core_1_discharge', 'core_1_distance',
            'core_2_discharge', 'core_2_distance', 'core_3_discharge', 'core_3_distance']
)

class CombinedPDMeasurementForm(forms.ModelForm):
    class Meta:
        model = PDDMeasurementSession
        fields = ['cable_line', 'session_date', 'notes']
        widgets = {
            'session_date': forms.DateInput(attrs={'type': 'date'}),
        }