import os
import django
from datetime import date, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cable_site.settings')
django.setup()

from cable_manager.models import Enterprise, CableLine, PDDMeasurementSession, SinglePDMeasurement, HighVoltageTest, \
    Accident, UserProfile
from django.contrib.auth.models import User


def create_test_data():
    """Создание тестовых данных для демонстрации"""

    # Создаем предприятие
    enterprise, created = Enterprise.objects.get_or_create(
        name="Энергосеть Сервис",
        address="г. Москва, ул. Энергетиков, 15"
    )

    # Создаем тестового пользователя
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={'email': 'demo@energoservice.ru'}
    )
    user.set_password('demo123')
    user.save()

    # Создаем профиль пользователя
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'enterprise': enterprise,
            'full_name': 'Иванов Алексей Петрович'
        }
    )

    # Создаем кабельные линии
    cables_data = [
        {'number': 'КЛ-001', 'brand': 'ААБл-10 3х120', 'length': 250, 'cores': 3},
        {'number': 'КЛ-002', 'brand': 'ААШв-10 3х150', 'length': 180, 'cores': 3},
        {'number': 'КЛ-003', 'brand': 'АВБбШв-10 3х95', 'length': 320, 'cores': 3},
        {'number': 'КЛ-004', 'brand': 'ПвБбШп-10 1х240', 'length': 150, 'cores': 1},
    ]

    cables = []
    for data in cables_data:
        cable, created = CableLine.objects.get_or_create(
            number=data['number'],
            defaults={
                'enterprise': enterprise,
                'cable_brand': data['brand'],
                'start_muff': 'КНТп-10',
                'end_muff': 'КНТп-10',
                'connect_muff_1': 'СТп-10',
                'length': data['length'],
                'core_count': data['cores'],
                'commissioning_date': date(2020, 1, 15)
            }
        )
        cables.append(cable)

    # Создаем сессии измерений ЧР
    for cable in cables:
        for i in range(2):  # По 2 сессии на каждый кабель
            session = PDDMeasurementSession.objects.create(
                cable_line=cable,
                session_date=date(2024, 1, 10) + timedelta(days=i * 30),
                notes=f"Плановые измерения {i + 1}"
            )

            # Создаем измерения при разных напряжениях
            for volt in [5, 10, 15]:
                measurement = SinglePDMeasurement.objects.create(
                    session=session,
                    voltage_level=volt,
                    core_1_discharge=random.uniform(10, 100),
                    core_1_distance=random.uniform(5, 50),
                    core_2_discharge=random.uniform(10, 100) if cable.core_count > 1 else None,
                    core_2_distance=random.uniform(5, 50) if cable.core_count > 1 else None,
                    core_3_discharge=random.uniform(10, 100) if cable.core_count > 2 else None,
                    core_3_distance=random.uniform(5, 50) if cable.core_count > 2 else None,
                )

    # Создаем высоковольтные испытания
    for cable in cables:
        HighVoltageTest.objects.create(
            cable_line=cable,
            test_date=date(2024, 1, 20),
            test_voltage=24,
            insulation_resistance=random.uniform(100, 1000)
        )

    # Создаем тестовую аварию
    Accident.objects.create(
        cable_line=cables[0],
        accident_date=date(2024, 2, 15),
        accident_type='short_circuit',
        description='Короткое замыкание на соединительной муфте',
        downtime=timedelta(hours=8)
    )

    print("Тестовые данные созданы!")
    print("Логин: demo_user")
    print("Пароль: demo123")


if __name__ == '__main__':
    create_test_data()