from django.apps import AppConfig


class CableManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cable_manager'

    def ready(self):
        # Автоматическое обучение модели при запуске сервера
        try:
            from .ai_analyzer import CableAIAnalyzer
            analyzer = CableAIAnalyzer()
            if analyzer.model is None:
                print("Попытка автоматического обучения ИИ-модели...")
                # Не будем автоматически обучать на синтетических данных
                # Пользователь сам решит, когда обучать модель
        except Exception as e:
            print(f"Ошибка при инициализации ИИ: {e}")