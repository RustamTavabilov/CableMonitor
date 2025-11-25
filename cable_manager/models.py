from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Enterprise(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название предприятия")
    address = models.TextField(blank=True, verbose_name="Адрес")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Предприятие'
        verbose_name_plural = 'Предприятия'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="Предприятие")
    full_name = models.CharField(max_length=255, verbose_name="ФИО")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


class CableLine(models.Model):
    number = models.CharField(max_length=100, unique=True, verbose_name="Номер кабельной линии")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="Предприятие")
    cable_brand = models.CharField(max_length=255, verbose_name="Марка кабеля")
    start_muff = models.CharField(max_length=255, verbose_name="Марка концевой муфты в начале")
    end_muff = models.CharField(max_length=255, verbose_name="Марка концевой муфты в конце")
    connect_muff_1 = models.CharField(max_length=255, blank=True, null=True, verbose_name="1-я соединительная муфта")
    connect_muff_2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="2-я соединительная муфта")
    connect_muff_3 = models.CharField(max_length=255, blank=True, null=True, verbose_name="3-я соединительная муфта")
    length = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Длина кабеля (м)")
    core_count = models.PositiveIntegerField(verbose_name="Количество жил")
    commissioning_date = models.DateField(verbose_name="Дата ввода в эксплуатацию")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")

    def __str__(self):
        return f"Линия {self.number} ({self.cable_brand})"

    class Meta:
        verbose_name = 'Кабельная линия'
        verbose_name_plural = 'Кабельные линии'


class MuffChangeLog(models.Model):
    cable_line = models.ForeignKey(CableLine, on_delete=models.CASCADE, verbose_name="Кабельная линия")
    change_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата изменения")
    changed_muff_type = models.CharField(max_length=50, choices=[
        ('start', 'Начальная концевая'),
        ('end', 'Конечная концевая'),
        ('conn1', 'Соединительная 1'),
        ('conn2', 'Соединительная 2'),
        ('conn3', 'Соединительная 3'),
    ], verbose_name="Тип измененной муфты")
    old_value = models.CharField(max_length=255, blank=True, null=True, verbose_name="Старое значение")
    new_value = models.CharField(max_length=255, verbose_name="Новое значение")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    def __str__(self):
        return f"Изменение муфты на {self.cable_line.number} ({self.change_date})"

    class Meta:
        verbose_name = 'История изменений муфт'
        verbose_name_plural = 'История изменений муфт'


class PDDMeasurementSession(models.Model):
    cable_line = models.ForeignKey(CableLine, on_delete=models.CASCADE, verbose_name="Кабельная линия")
    session_date = models.DateField(verbose_name="Дата измерений")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    notes = models.TextField(blank=True, verbose_name="Примечания к серии измерений")

    def __str__(self):
        return f"Сессия ЧР {self.cable_line.number} от {self.session_date}"

    class Meta:
        verbose_name = 'Сессия измерений ЧР'
        verbose_name_plural = 'Сессии измерений ЧР'


class SinglePDMeasurement(models.Model):
    session = models.ForeignKey(PDDMeasurementSession, on_delete=models.CASCADE, verbose_name="Сессия измерений")
    voltage_level = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Уровень напряжения (кВ)")

    core_1_discharge = models.FloatField(blank=True, null=True, verbose_name="ЧР на жиле 1 (пКл)")
    core_1_distance = models.FloatField(blank=True, null=True, verbose_name="Расстояние ЧР на жиле 1 (м)")
    core_2_discharge = models.FloatField(blank=True, null=True, verbose_name="ЧР на жиле 2 (пКл)")
    core_2_distance = models.FloatField(blank=True, null=True, verbose_name="Расстояние ЧР на жиле 2 (м)")
    core_3_discharge = models.FloatField(blank=True, null=True, verbose_name="ЧР на жиле 3 (пКл)")
    core_3_distance = models.FloatField(blank=True, null=True, verbose_name="Расстояние ЧР на жиле 3 (м)")

    def __str__(self):
        return f"Измерение при {self.voltage_level} кВ (сессия {self.session.id})"

    class Meta:
        verbose_name = 'Измерение ЧР при напряжении'
        verbose_name_plural = 'Измерения ЧР при напряжениях'


class HighVoltageTest(models.Model):
    cable_line = models.ForeignKey(CableLine, on_delete=models.CASCADE, verbose_name="Кабельная линия")
    test_date = models.DateField(verbose_name="Дата испытания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    test_voltage = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Испытательное напряжение (кВ)")
    insulation_resistance = models.FloatField(validators=[MinValueValidator(0.0)],
                                              verbose_name="Сопротивление изоляции (МОм)")

    def __str__(self):
        return f"ВИ для {self.cable_line.number} от {self.test_date}"

    class Meta:
        verbose_name = 'Высоковольтное испытание'
        verbose_name_plural = 'Высоковольтные испытания'


class Accident(models.Model):
    ACCIDENT_TYPES = [
        ('short_circuit', 'Короткое замыкание'),
        ('break', 'Обрыв'),
        ('insulation_breakdown', 'Пробой изоляции на муфте'),
        ('other', 'Другое'),
    ]

    cable_line = models.ForeignKey(CableLine, on_delete=models.CASCADE, verbose_name="Кабельная линия")
    accident_date = models.DateTimeField(verbose_name="Дата и время аварии")
    accident_type = models.CharField(max_length=50, choices=ACCIDENT_TYPES, verbose_name="Тип аварии")
    description = models.TextField(verbose_name="Описание аварии")
    downtime = models.DurationField(blank=True, null=True, verbose_name="Время простоя")

    def __str__(self):
        return f"Авария на {self.cable_line.number} ({self.accident_date})"

    class Meta:
        verbose_name = 'Авария'
        verbose_name_plural = 'Аварии'