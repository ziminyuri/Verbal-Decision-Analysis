import os
from random import randint

from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import View

from services.model import create_model, get_model_data
from services.pairs_of_options import create_files
from services.services import get_userprofile


from .tasks import delete_model

from .models import Model


class LoginView(View):
    """ Aвторизация """

    def get(self, request):

        return render(request, "auth.html", {"login_error": ''})

    def post(self, request):
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
                return redirect("users_list")
            else:
                return redirect("index")

        else:
            login_error = f'Неверный логин или пароль! Повторите попытку.'
            return render(request, "auth.html", {"login_error": login_error})


class RegistrationView(View):
    """ Регистрация """

    def get(self, request):
        return render(request, "registration.html", {'error': None})

    def post(self, request):
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        password_2 = request.POST.get("password_2")

        if password != password_2:
            error = 'Пароли не совпадают'
            return render(request, "registration.html", {'error': error})

        user = User.objects.filter(username=email)
        if not user:
            User.objects.create_user(email, email, password)
            auth.authenticate(username=email, password=password)
            return redirect('login')
        else:
            error = 'Пользователь с таким e-mail существует'
            return render(request, "registration.html", {'error': error})


class LogoutView(View):
    """ Выход из системы """

    def get(self, request):
        django_logout(request)
        return redirect("login")


class IndexView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        return render(request, "index.html", {})


class DemoModelCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        return render(request, "model/demo_choice_number.html", {})

    def post(self, request):
        user_profile = get_userprofile(request)
        number_of_alternatives = int(request.POST['number'])
        create_model.delay(user_profile.id, demo_model=True, number_of_alternatives=number_of_alternatives)
        return redirect('models')


class UploadView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        r_int = str(randint(0, 100))
        path_csv = f'{request.user.username}/{r_int}{uploaded_file.name}'
        fs.save(path_csv, uploaded_file)
        user_profile = get_userprofile(request)
        model = create_model(user_profile.id, demo_model=False, path_csv=path_csv)
        if model is False:
            error = 'Возникла ошибка при загрузке файла. Проверьте файл'
            return render(request, "upload_model.html", {'error': error})
        create_files(model)
        return redirect('models_id', id=model.id)

    def get(self, request):
        return render(request, "upload_model.html", {})


class DownloadCSVView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        file_path = 'media/demo/demo.csv'
        data = open(file_path, "rb").read()
        response = HttpResponse(data, content_type='application;')
        response['Content-Length'] = os.path.getsize(file_path)
        response['Content-Disposition'] = 'attachment; filename=%s' % 'demo.csv'

        return response


class ModelCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        number_for_select = list(range(1, 11))
        return render(request, "model/choice_number.html", {'number_for_select': number_for_select})

    def post(self, request):
        """ Данные для заполнения таблицы """

        number_of_criterion = int(request.POST["number_of_criterion"])
        number_of_alternatives = int(request.POST["number_of_alternatives"])
        number_of_criterion_for_select = list(range(1, number_of_criterion + 1))
        number_of_alternatives_for_select = list(range(1, number_of_alternatives + 1))
        return render(request, "model/input_data.html",
                      {'number_of_criterion_for_select': number_of_criterion_for_select,
                       'number_of_alternatives_for_select': number_of_alternatives_for_select,
                       'number_of_criterion': number_of_criterion,
                       'number_of_alternatives': number_of_alternatives,
                       'error': None})


class ModelListCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request):
        from django.db.models import Count
        user = get_userprofile(request)
        models = Model.objects.filter(id_user=user).annotate(numbers=Count('model')).order_by('id')
        return render(request, "model/models.html", {'models': models})

    @staticmethod
    def post(request):
        """ Cоздание модели после ввода данных в таблице """

        user_profile = get_userprofile(request)
        model = create_model(user_profile.id, demo_model=False, request=request)

        if model is not False:
            create_files(model)
            return redirect('models_id', id=model.id)

        else:
            number_of_criterion = request.POST["number_of_criterion"]
            number_of_alternatives = request.POST["number_of_alternatives"]
            number_of_criterion_for_select = list(range(1, int(number_of_criterion) + 1))
            number_of_alternatives_for_select = list(range(1, int(number_of_alternatives) + 1))
            return render(request, "model/input_data.html",
                          {'number_of_criterion_for_select': number_of_criterion_for_select,
                           'number_of_alternatives_for_select': number_of_alternatives_for_select,
                           'error': "Ошибка при заполнении. Повторите попытку ввода"})


class ModelView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        try:
            model = Model.objects.get(id=id)
            model_data, model_header = get_model_data(model.id)
            return render(request, "model/model.html",
                          {'model_data': model_data,
                           'model_header': model_header,
                           'model': model})
        except:
            return redirect('models')

    @staticmethod
    def post(request, id):
        """ Delete model """
        if request.POST["_method"] == 'DELETE':
            Model.objects.filter(id=id).update(is_delete=True)
            delete_model.delay(id)
            return redirect('models')


class ModelDemoVKRCreateView(View):
    def get(self, request):
        """Создание модели: выбор 1 конмнатной квартиры"""
        user_profile = get_userprofile(request)
        create_model.delay(user_profile.id, demo_model=True, demo_vkr=True)
        return redirect('models')




