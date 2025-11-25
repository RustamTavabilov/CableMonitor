from .ai_analyzer import CableAIAnalyzer
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import inlineformset_factory
from .models import CableLine, PDDMeasurementSession, HighVoltageTest, Accident, Enterprise, SinglePDMeasurement
from .forms import CableLineForm, PDDMeasurementSessionForm, HighVoltageTestForm, AccidentForm, MuffChangeLogForm, \
    SinglePDMeasurementForm


def home(request):
    return render(request, 'cable_manager/home.html')


@login_required
def ai_analysis(request):
    """Страница ИИ-анализа"""
    analyzer = CableAIAnalyzer()

    # Проверяем, обучена ли модель
    model_trained = analyzer.model is not None

    # Анализ рисков для кабельных линий пользователя
    user_enterprise = request.user.userprofile.enterprise
    cable_lines = CableLine.objects.filter(enterprise=user_enterprise)

    risk_analysis = []
    for cable in cable_lines:
        risk_level, probability = analyzer.predict_risk(cable)
        risk_analysis.append({
            'cable': cable,
            'risk_level': risk_level,
            'probability': f"{probability:.1%}",
            'color': 'green' if risk_level == 'Низкий' else 'orange' if risk_level == 'Средний' else 'red'
        })

    # Важность признаков
    feature_importance = analyzer.get_feature_importance()

    context = {
        'model_trained': model_trained,
        'risk_analysis': risk_analysis,
        'feature_importance': feature_importance,
    }

    return render(request, 'cable_manager/ai_analysis.html', context)


@login_required
def statistics(request):
    """Страница со статистикой"""
    user_enterprise = request.user.userprofile.enterprise
    cable_lines = CableLine.objects.filter(enterprise=user_enterprise)

    # Основная статистика
    total_cables = cable_lines.count()
    total_measurements = PDDMeasurementSession.objects.filter(cable_line__in=cable_lines).count()
    total_tests = HighVoltageTest.objects.filter(cable_line__in=cable_lines).count()
    total_accidents = Accident.objects.filter(cable_line__in=cable_lines).count()

    # Анализ рисков
    analyzer = CableAIAnalyzer()
    risk_distribution = {'Низкий': 0, 'Средний': 0, 'Высокий': 0}

    for cable in cable_lines:
        risk_level, _ = analyzer.predict_risk(cable)
        if risk_level in risk_distribution:
            risk_distribution[risk_level] += 1

    context = {
        'total_cables': total_cables,
        'total_measurements': total_measurements,
        'total_tests': total_tests,
        'total_accidents': total_accidents,
        'risk_distribution': risk_distribution,
        'cable_lines': cable_lines,
    }

    return render(request, 'cable_manager/statistics.html', context)

@login_required
def train_ai_model(request):
    """Обучение ИИ-модели"""
    analyzer = CableAIAnalyzer()

    # Сначала пробуем обучить на реальных данных
    success = analyzer.train_model()

    if not success:
        # Если реальных данных недостаточно, используем синтетические для демонстрации
        messages.info(request, 'Недостаточно реальных данных. Используются демонстрационные данные.')
        success = analyzer.train_with_synthetic_data()

    if success:
        messages.success(request, 'Модель ИИ успешно обучена!')
    else:
        messages.warning(request, 'Не удалось обучить модель')

    return redirect('ai_analysis')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'cable_manager/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    user_enterprise = request.user.userprofile.enterprise
    cable_lines = CableLine.objects.filter(enterprise=user_enterprise)

    context = {
        'cable_lines': cable_lines,
        'enterprise': user_enterprise
    }
    return render(request, 'cable_manager/dashboard.html', context)


@login_required
def add_cable_line(request):
    if request.method == 'POST':
        form = CableLineForm(request.POST)
        if form.is_valid():
            cable_line = form.save(commit=False)
            cable_line.enterprise = request.user.userprofile.enterprise
            cable_line.save()
            messages.success(request, 'Кабельная линия успешно добавлена')
            return redirect('dashboard')
    else:
        form = CableLineForm()

    return render(request, 'cable_manager/add_cable_line.html', {'form': form})


@login_required
def add_measurement_session(request):
    user_enterprise = request.user.userprofile.enterprise
    cable_lines = CableLine.objects.filter(enterprise=user_enterprise)

    PDMeasurementFormSet = inlineformset_factory(
        PDDMeasurementSession,
        SinglePDMeasurement,
        form=SinglePDMeasurementForm,
        extra=3,
        can_delete=True,
        fields=['voltage_level', 'core_1_discharge', 'core_1_distance',
                'core_2_discharge', 'core_2_distance', 'core_3_discharge', 'core_3_distance']
    )

    if request.method == 'POST':
        session_form = PDDMeasurementSessionForm(request.POST)
        formset = PDMeasurementFormSet(request.POST)

        if session_form.is_valid() and formset.is_valid():
            session = session_form.save()

            measurements = formset.save(commit=False)
            for measurement in measurements:
                measurement.session = session
                measurement.save()

            for measurement in formset.deleted_objects:
                measurement.delete()

            messages.success(request, 'Сессия измерений с данными по напряжениям успешно добавлена')
            return redirect('dashboard')
    else:
        session_form = PDDMeasurementSessionForm()
        formset = PDMeasurementFormSet()
        session_form.fields['cable_line'].queryset = cable_lines

    context = {
        'form': session_form,
        'formset': formset,
    }
    return render(request, 'cable_manager/add_measurement_session.html', context)


@login_required
def add_high_voltage_test(request):
    user_enterprise = request.user.userprofile.enterprise
    cable_lines = CableLine.objects.filter(enterprise=user_enterprise)

    if request.method == 'POST':
        form = HighVoltageTestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Результаты испытаний добавлены')
            return redirect('dashboard')
    else:
        form = HighVoltageTestForm()
        form.fields['cable_line'].queryset = cable_lines

    return render(request, 'cable_manager/add_high_voltage_test.html', {'form': form})


@login_required
def cable_line_detail(request, cable_id):
    try:
        cable_line = CableLine.objects.get(id=cable_id)
        measurements = PDDMeasurementSession.objects.filter(cable_line=cable_line).prefetch_related(
            'singlepdmeasurement_set')
        tests = HighVoltageTest.objects.filter(cable_line=cable_line)
        accidents = Accident.objects.filter(cable_line=cable_line)

        context = {
            'cable_line': cable_line,
            'measurements': measurements,
            'tests': tests,
            'accidents': accidents,
        }
        return render(request, 'cable_manager/cable_line_detail.html', context)
    except CableLine.DoesNotExist:
        messages.error(request, 'Кабельная линия не найдена')
        return redirect('dashboard')