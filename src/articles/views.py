from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from .models import Article


def archive(request):
    return render(request, 'archive.html', {'posts': Article.objects.all()})


def get_article(request, article_id):
    post = get_object_or_404(Article, id=article_id)
    return render(request, 'article.html', {'post': post})


def create_post(request):
    if not request.user.is_authenticated:
        raise Http404

    form = {'title': '', 'text': '', 'errors': ''}
    if request.method == 'POST':
        form['title'] = request.POST.get('title', '').strip()
        form['text'] = request.POST.get('text', '').strip()
        if not form['title'] or not form['text']:
            form['errors'] = 'Не все поля заполнены'
        elif len(form['title']) > 200:
            form['errors'] = 'Название не должно быть длиннее 200 символов'
        elif any(title.casefold() == form['title'].casefold()
                 for title in Article.objects.values_list('title', flat=True)):
            form['errors'] = 'Статья с таким названием уже существует'
        else:
            post = Article.objects.create(
                title=form['title'], text=form['text'], author=request.user
            )
            return redirect('get_article', article_id=post.id)
    return render(request, 'create_post.html', {'form': form})


def register_user(request):
    form = {'username': '', 'email': '', 'error': ''}
    if request.method == 'POST':
        form['username'] = request.POST.get('username', '').strip()
        form['email'] = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        if not form['username'] or not form['email'] or not password.strip():
            form['error'] = 'Заполните все поля'
        elif len(form['username']) > 150 or len(form['email']) > 254:
            form['error'] = 'Имя пользователя или адрес электронной почты слишком длинные'
        elif any(name.casefold() == form['username'].casefold()
                 for name in User.objects.values_list('username', flat=True)):
            form['error'] = 'Пользователь с таким именем уже существует'
        else:
            try:
                User._meta.get_field('username').run_validators(form['username'])
                validate_email(form['email'])
            except ValidationError:
                form['error'] = 'Проверьте имя пользователя и адрес электронной почты'
            else:
                User.objects.create_user(
                    username=form['username'], email=form['email'], password=password
                )
                messages.success(request, 'Регистрация завершена. Войдите в аккаунт.')
                return redirect('login')
    return render(request, 'register.html', {'form': form})


def login_user(request):
    form = {'username': '', 'error': ''}
    if request.method == 'POST':
        form['username'] = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if not form['username'] or not password.strip():
            form['error'] = 'Заполните все поля'
        else:
            user = authenticate(request, username=form['username'], password=password)
            if user is None:
                form['error'] = 'Неверное имя пользователя или пароль'
            else:
                login(request, user)
                return redirect('archive')
    return render(request, 'login.html', {'form': form})


@require_POST
def logout_user(request):
    logout(request)
    return redirect('archive')
