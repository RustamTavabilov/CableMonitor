from django.contrib import admin
from .models import *

class SinglePDMeasurementInline(admin.TabularInline):
    model = SinglePDMeasurement
    extra = 1
    fields = ['voltage_level', 'core_1_discharge', 'core_1_distance', 'core_2_discharge', 'core_2_distance', 'core_3_discharge', 'core_3_distance']

class PDDMeasurementSessionAdmin(admin.ModelAdmin):
    inlines = [SinglePDMeasurementInline]
    list_display = ['cable_line', 'session_date', 'created_at']
    list_filter = ['session_date', 'cable_line']
    date_hierarchy = 'session_date'

class CableLineAdmin(admin.ModelAdmin):
    list_display = ['number', 'cable_brand', 'enterprise', 'commissioning_date', 'length']
    list_filter = ['enterprise', 'commissioning_date']
    search_fields = ['number', 'cable_brand']
    date_hierarchy = 'commissioning_date'

class HighVoltageTestAdmin(admin.ModelAdmin):
    list_display = ['cable_line', 'test_date', 'test_voltage', 'insulation_resistance']
    list_filter = ['test_date', 'cable_line']
    date_hierarchy = 'test_date'

class AccidentAdmin(admin.ModelAdmin):
    list_display = ['cable_line', 'accident_date', 'accident_type']
    list_filter = ['accident_date', 'accident_type']
    date_hierarchy = 'accident_date'

class MuffChangeLogAdmin(admin.ModelAdmin):
    list_display = ['cable_line', 'change_date', 'changed_muff_type', 'new_value']
    list_filter = ['change_date', 'changed_muff_type']
    date_hierarchy = 'change_date'

admin.site.register(Enterprise)
admin.site.register(UserProfile)
admin.site.register(CableLine, CableLineAdmin)
admin.site.register(MuffChangeLog, MuffChangeLogAdmin)
admin.site.register(PDDMeasurementSession, PDDMeasurementSessionAdmin)
admin.site.register(SinglePDMeasurement)
admin.site.register(HighVoltageTest, HighVoltageTestAdmin)
admin.site.register(Accident, AccidentAdmin)