import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from .models import CableLine, PDDMeasurementSession, SinglePDMeasurement, HighVoltageTest, Accident
from django.conf import settings
from datetime import timedelta
from django.utils import timezone


class CableAIAnalyzer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = os.path.join(settings.BASE_DIR, 'cable_ai_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'cable_scaler.pkl')
        self.load_model()

    def prepare_training_data(self):
        """Подготовка данных для обучения модели"""
        features = []
        labels = []

        print("Сбор данных для обучения...")

        # Собираем данные по всем кабельным линиям
        cable_lines = CableLine.objects.all()

        print(f"Найдено кабельных линий: {cable_lines.count()}")

        for cable in cable_lines:
            # Получаем ВСЕ сессии измерений для этого кабеля
            sessions = PDDMeasurementSession.objects.filter(cable_line=cable).order_by('session_date')

            for session in sessions:
                # Получаем все измерения для этой сессии
                measurements = SinglePDMeasurement.objects.filter(session=session)

                if not measurements:
                    continue

                # Извлекаем признаки
                feature_vector = self.extract_features(cable, measurements)

                if feature_vector is not None:
                    features.append(feature_vector)

                    # Определяем метку (была ли авария в ближайшие 90 дней после измерений)
                    has_accident = self.check_future_accidents(cable, session.session_date)
                    labels.append(1 if has_accident else 0)

        print(f"Подготовлено образцов: {len(features)}")
        print(f"Аварии в данных: {sum(labels)}")

        return np.array(features), np.array(labels)

    def extract_features(self, cable, measurements):
        """Извлечение признаков из данных измерений"""
        try:
            features = []

            # Базовые параметры кабеля
            features.extend([
                cable.length,
                cable.core_count,
                (timezone.now().date() - cable.commissioning_date).days  # возраст кабеля в днях
            ])

            # Статистики по измерениям ЧР
            voltages = []
            discharges_core1 = []
            discharges_core2 = []
            discharges_core3 = []
            distances_core1 = []
            distances_core2 = []
            distances_core3 = []

            for measurement in measurements:
                voltages.append(measurement.voltage_level)

                # Собираем данные по каждой жиле отдельно
                if measurement.core_1_discharge:
                    discharges_core1.append(measurement.core_1_discharge)
                if measurement.core_1_distance:
                    distances_core1.append(measurement.core_1_distance)

                if measurement.core_2_discharge:
                    discharges_core2.append(measurement.core_2_discharge)
                if measurement.core_2_distance:
                    distances_core2.append(measurement.core_2_distance)

                if measurement.core_3_discharge:
                    discharges_core3.append(measurement.core_3_discharge)
                if measurement.core_3_distance:
                    distances_core3.append(measurement.core_3_distance)

            # Добавляем статистики по напряжениям
            features.extend([
                np.mean(voltages) if voltages else 0,
                np.max(voltages) if voltages else 0,
                np.min(voltages) if voltages else 0,
                np.std(voltages) if voltages else 0,
            ])

            # Добавляем статистики по ЧР для каждой жилы
            for discharges, distances in [(discharges_core1, distances_core1),
                                          (discharges_core2, distances_core2),
                                          (discharges_core3, distances_core3)]:
                features.extend([
                    np.mean(discharges) if discharges else 0,
                    np.max(discharges) if discharges else 0,
                    np.mean(distances) if distances else 0,
                    np.max(distances) if distances else 0,
                ])

            # Общее количество измерений
            features.append(len(measurements))

            return features

        except Exception as e:
            print(f"Ошибка при извлечении признаков: {e}")
            return None

    def check_future_accidents(self, cable, measurement_date):
        """Проверяет, были ли аварии в течение 90 дней после измерений"""
        future_date = measurement_date + timedelta(days=90)
        accidents = Accident.objects.filter(
            cable_line=cable,
            accident_date__date__gte=measurement_date,
            accident_date__date__lte=future_date
        )
        return accidents.exists()

    def train_model(self):
        """Обучение модели"""
        print("Начинаем обучение модели ИИ...")

        features, labels = self.prepare_training_data()

        if len(features) < 5:
            print(f"Недостаточно данных для обучения. Нужно минимум 5 образцов, доступно: {len(features)}")
            return False

        # Масштабирование признаков
        features_scaled = self.scaler.fit_transform(features)

        # Для маленьких наборов данных используем другую стратегию
        if len(features) < 10:
            # Используем все данные для обучения без разделения
            X_train = features_scaled
            y_train = labels
            X_test = features_scaled
            y_test = labels
            print("Используется обучение на всех данных (мало образцов)")
        else:
            # Разделение на обучающую и тестовую выборки
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, labels, test_size=0.2, random_state=42
            )
            print(f"Разделение данных: {len(X_train)} train, {len(X_test)} test")

        # Обучение модели
        self.model = RandomForestClassifier(
            n_estimators=50,  # Уменьшаем для маленьких наборов данных
            max_depth=5,
            random_state=42,
            min_samples_split=2,
            min_samples_leaf=1
        )

        self.model.fit(X_train, y_train)

        # Оценка модели
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Точность модели: {accuracy:.2f}")
        if len(set(y_test)) > 1:  # Проверяем, есть ли более одного класса в тестовых данных
            print("Отчет классификации:")
            print(classification_report(y_test, y_pred))

        # Сохранение модели
        self.save_model()

        return True

    def predict_risk(self, cable_line):
        """Прогнозирование риска аварии для конкретной кабельной линии"""
        if self.model is None:
            return "Модель не обучена", 0

        # Получаем последние измерения
        latest_session = PDDMeasurementSession.objects.filter(
            cable_line=cable_line
        ).order_by('-session_date').first()

        if not latest_session:
            return "Нет данных измерений", 0

        measurements = SinglePDMeasurement.objects.filter(session=latest_session)

        if not measurements:
            return "Нет данных измерений", 0

        # Извлекаем признаки
        feature_vector = self.extract_features(cable_line, measurements)

        if feature_vector is None:
            return "Ошибка извлечения признаков", 0

        # Масштабируем и предсказываем
        try:
            feature_vector_scaled = self.scaler.transform([feature_vector])
            probability = self.model.predict_proba(feature_vector_scaled)[0][1]
        except Exception as e:
            print(f"Ошибка предсказания: {e}")
            return "Ошибка предсказания", 0

        # Определяем уровень риска
        if probability < 0.3:
            risk_level = "Низкий"
        elif probability < 0.7:
            risk_level = "Средний"
        else:
            risk_level = "Высокий"

        return risk_level, probability

    def save_model(self):
        """Сохранение обученной модели"""
        if self.model is not None:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            print("Модель сохранена")

    def load_model(self):
        """Загрузка обученной модели"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                print("Модель загружена")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            self.model = None

    def get_feature_importance(self):
        """Получение важности признаков"""
        if self.model is None:
            return []

        feature_names = [
            'Длина кабеля', 'Количество жил', 'Возраст кабеля',
            'Среднее напряжение', 'Максимальное напряжение', 'Минимальное напряжение',
            'Стандартное отклонение напряжения',
            'Средний ЧР жила 1', 'Максимальный ЧР жила 1', 'Среднее расстояние жила 1',
            'Максимальное расстояние жила 1',
            'Средний ЧР жила 2', 'Максимальный ЧР жила 2', 'Среднее расстояние жила 2',
            'Максимальное расстояние жила 2',
            'Средний ЧР жила 3', 'Максимальный ЧР жила 3', 'Среднее расстояние жила 3',
            'Максимальное расстояние жила 3',
            'Количество измерений'
        ]

        importances = self.model.feature_importances_
        return list(zip(feature_names, importances))

    def generate_synthetic_data(self, num_samples=20):
        """Генерация синтетических данных для демонстрации (только для тестирования)"""
        print("Генерация синтетических данных для демонстрации...")

        features = []
        labels = []

        # Генерируем реалистичные данные
        for i in range(num_samples):
            # Случайные параметры кабеля
            length = np.random.uniform(100, 1000)
            core_count = np.random.choice([1, 3, 5])
            age = np.random.uniform(0, 3650)  # до 10 лет

            # Случайные измерения ЧР
            avg_voltage = np.random.uniform(1, 35)
            max_voltage = avg_voltage + np.random.uniform(0, 10)

            # Высокие значения ЧР увеличивают вероятность аварии
            avg_discharge = np.random.exponential(50)
            max_discharge = avg_discharge + np.random.exponential(20)

            feature_vector = [
                length, core_count, age,
                avg_voltage, max_voltage, avg_voltage - 5, 2.0,  # напряжения
                avg_discharge, max_discharge, 50, 100,  # жила 1
                                          avg_discharge * 0.8, max_discharge * 0.8, 45, 90,  # жила 2
                                          avg_discharge * 0.6, max_discharge * 0.6, 40, 80,  # жила 3
                3  # количество измерений
            ]

            features.append(feature_vector)

            # Вероятность аварии зависит от уровня ЧР и возраста
            accident_prob = min(0.9, (avg_discharge / 100) * (age / 3650))
            labels.append(1 if np.random.random() < accident_prob else 0)

        return np.array(features), np.array(labels)

    def train_with_synthetic_data(self):
        """Обучение на синтетических данных для демонстрации"""
        print("Обучение на синтетических данных...")

        features, labels = self.generate_synthetic_data(50)

        # Масштабирование признаков
        features_scaled = self.scaler.fit_transform(features)

        # Обучение модели
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        self.model.fit(features_scaled, labels)

        # Сохранение модели
        self.save_model()

        print("Модель обучена на синтетических данных")
        return True