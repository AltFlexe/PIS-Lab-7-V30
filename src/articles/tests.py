from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import Article, Space, Tenant, Contract, ContractSpace, Payment


class ArticleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student')

    def test_excerpt_and_author(self):
        article = Article.objects.create(title='Тест', author=self.user, text='а' * 141)
        self.assertEqual(article.get_excerpt(), 'а' * 140 + '...')
        self.assertEqual(str(article), 'student: Тест')
        article.text = 'Короткая статья'
        self.assertEqual(article.get_excerpt(), 'Короткая статья')

    def test_archive(self):
        Article.objects.create(title='Первая статья', author=self.user, text='Учебный текст')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Первая статья')
        self.assertContains(response, 'student')
        self.assertContains(response, 'Учебный текст')
        self.assertContains(response, '/static/img/logo.svg')


class RentalTests(TestCase):
    def setUp(self):
        self.space = Space.objects.create(number='A-101', floor=1, area=25, air_conditioner=True, daily_price=1200)
        self.other = Space.objects.create(number='A-102', floor=1, area=32, air_conditioner=True, daily_price=1500)
        self.tenant = Tenant.objects.create(name='Магазин', address='Учебный адрес', phone='000', details='Учебные реквизиты', contact='Контакт')
        self.contract = Contract.objects.create(number='Д-1', tenant=self.tenant, signed_date=date(2026, 1, 1))
        self.period = ContractSpace.objects.create(contract=self.contract, space=self.space,
                                                   start_date=date(2026, 2, 1), end_date=date(2026, 2, 28))

    def test_multiple_spaces_and_signed_date(self):
        ContractSpace.objects.create(contract=self.contract, space=self.other,
                                     start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        self.assertEqual(self.contract.periods.count(), 2)
        self.assertLess(self.contract.signed_date, self.period.start_date)

    def test_overlap_and_boundaries(self):
        with self.assertRaises(ValidationError):
            ContractSpace.objects.create(contract=self.contract, space=self.space,
                                         start_date=date(2026, 2, 28), end_date=date(2026, 3, 3))
        ContractSpace.objects.create(contract=self.contract, space=self.space,
                                     start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        self.assertNotIn(self.space, Space.available(date(2026, 2, 28), date(2026, 2, 28)))
        self.assertIn(self.other, Space.available(date(2026, 2, 28), date(2026, 2, 28)))

    def test_gap_is_available(self):
        ContractSpace.objects.create(contract=self.contract, space=self.space,
                                     start_date=date(2026, 4, 1), end_date=date(2026, 4, 30))
        self.assertIn(self.space, Space.available(date(2026, 3, 1), date(2026, 3, 31)))

    def test_invalid_period(self):
        with self.assertRaises(ValidationError):
            ContractSpace.objects.create(contract=self.contract, space=self.other,
                                         start_date=date(2026, 4, 3), end_date=date(2026, 4, 1))
        with self.assertRaises(ValidationError):
            Space.available(date(2026, 4, 3), date(2026, 4, 1))

    def test_bulk_insert_cannot_bypass_database_guard(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ContractSpace.objects.bulk_create([ContractSpace(contract=self.contract, space=self.space,
                start_date=date(2026, 2, 15), end_date=date(2026, 3, 1))])

    def test_update_cannot_bypass_database_guard(self):
        other = ContractSpace.objects.create(contract=self.contract, space=self.space,
                                             start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        with self.assertRaises(IntegrityError), transaction.atomic():
            ContractSpace.objects.filter(pk=other.pk).update(start_date=date(2026, 2, 20))

    def test_payment_belongs_to_contract(self):
        payment = Payment.objects.create(contract=self.contract, month=date(2026, 2, 1),
                                         paid_date=date(2026, 2, 5), amount=Decimal('10000.00'))
        self.assertEqual(self.contract.payments.get(), payment)



from django.urls import reverse



class ArticlePageTests(TestCase):
    def setUp(self):
        author = User.objects.create_user(username='student')
        self.first = Article.objects.create(title='Лес весной', author=author, text='Длинный текст. ' * 15)
        self.second = Article.objects.create(title='Чистая река', author=author, text='Текст второй статьи')

    def test_archive_links_and_excerpt(self):
        response = self.client.get(reverse('archive'))
        for article in (self.first, self.second):
            self.assertContains(response, reverse('get_article', args=[article.id]))
            self.assertContains(response, article.title)
        self.assertContains(response, self.first.get_excerpt())
        self.assertNotContains(response, self.first.text)

    def test_each_article_full_text_and_back_link(self):
        for article in (self.first, self.second):
            response = self.client.get(reverse('get_article', args=[article.id]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, article.title)
            self.assertContains(response, article.text)
            self.assertContains(response, 'Все записи')
            self.assertContains(response, 'href="/"')

    def test_missing_and_invalid_routes(self):
        self.assertEqual(self.client.get('/article/99999/').status_code, 404)
        self.assertEqual(self.client.get('/article/abc/').status_code, 404)
        self.assertEqual(self.client.get('/artikle/1/').status_code, 404)


class CreatePostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author')
        self.existing = Article.objects.create(title='Первый пост', author=self.user, text='Текст')
        self.url = reverse('create_post')

    def test_anonymous_get_and_post_are_unavailable(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {'title': 'А', 'text': 'Б'}).status_code, 404)
        self.assertEqual(Article.objects.count(), 1)

    def test_get_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'Написать статью')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_missing_fields_and_whitespace(self):
        self.client.force_login(self.user)
        for data in ({'title': '', 'text': 'Текст'}, {'title': 'Заголовок', 'text': '   '}, {}):
            response = self.client.post(self.url, data)
            self.assertContains(response, 'Не все поля заполнены')
        self.assertEqual(Article.objects.count(), 1)

    def test_duplicate_title_and_preserved_values(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'title': 'Первый пост', 'text': 'Новый текст'})
        self.assertContains(response, 'Статья с таким названием уже существует')
        self.assertContains(response, 'Новый текст')
        response = self.client.post(self.url, {'title': 'ПЕРВЫЙ ПОСТ', 'text': 'Текст'})
        self.assertContains(response, 'Статья с таким названием уже существует')
        self.assertEqual(Article.objects.count(), 1)

    def test_too_long_title(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'title': 'А' * 201, 'text': 'Текст'})
        self.assertContains(response, 'Название не должно быть длиннее 200 символов')
        self.assertEqual(Article.objects.count(), 1)

    def test_create_multiple_and_redirect(self):
        self.client.force_login(self.user)
        for title in ('Вторая статья', 'Третья статья'):
            response = self.client.post(self.url, {'title': title, 'text': 'Учебный текст'})
            article = Article.objects.get(title=title)
            self.assertEqual(article.author, self.user)
            self.assertRedirects(response, reverse('get_article', args=[article.id]))
            self.assertContains(self.client.get(reverse('archive')), title)
        self.assertEqual(Article.objects.count(), 3)


class AccountsTests(TestCase):
    def setUp(self):
        import secrets
        self.password = secrets.token_urlsafe(18)
        self.existing = User.objects.create_user(username='Пользователь', email='one@example.test', password=self.password)
        Article.objects.create(title='Статья', author=self.existing, text='Текст')

    def test_register_empty_fields(self):
        for data in ({}, {'username': 'new', 'email': 'new@example.test'},
                     {'username': 'new', 'password': self.password},
                     {'email': 'new@example.test', 'password': self.password}):
            response = self.client.post(reverse('register'), data)
            self.assertContains(response, 'Заполните все поля')
        self.assertEqual(User.objects.count(), 1)

    def test_register_duplicate_and_invalid_email(self):
        response = self.client.post(reverse('register'), {'username': 'ПОЛЬЗОВАТЕЛЬ', 'email': 'two@example.test', 'password': self.password})
        self.assertContains(response, 'Пользователь с таким именем уже существует')
        response = self.client.post(reverse('register'), {'username': 'new', 'email': 'wrong', 'password': self.password})
        self.assertContains(response, 'Проверьте имя пользователя и адрес электронной почты')
        self.assertEqual(User.objects.count(), 1)

    def test_registration_saves_hashed_password(self):
        response = self.client.post(reverse('register'), {'username': 'newuser', 'email': 'new@example.test', 'password': self.password})
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'new@example.test')
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)

    def test_login_invalid_empty_and_correct(self):
        response = self.client.post(reverse('login'), {'username': 'Пользователь', 'password': ''})
        self.assertContains(response, 'Заполните все поля')
        response = self.client.post(reverse('login'), {'username': 'Пользователь', 'password': self.password + '_invalid'})
        self.assertContains(response, 'Неверное имя пользователя или пароль')
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.post(reverse('login'), {'username': 'Пользователь', 'password': self.password})
        self.assertRedirects(response, reverse('archive'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.existing.id)
        self.assertEqual(self.client.get(reverse('create_post')).status_code, 200)

    def test_logout_restores_anonymous_access(self):
        self.client.force_login(self.existing)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('archive'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('create_post')).status_code, 404)

    def test_registration_link_on_archive_and_article(self):
        for path in (reverse('archive'), reverse('get_article', args=[1])):
            response = self.client.get(path)
            self.assertContains(response, 'href="/register/"')
            self.assertContains(response, 'Регистрация')
            self.assertContains(response, 'Войти')

    def test_registration_form_csrf_protected(self):
        from django.test import Client
        protected = Client(enforce_csrf_checks=True)
        response = protected.post(reverse('register'), {'username': 'new', 'email': 'new@example.test', 'password': self.password})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='new').exists())


class JavaScriptArchiveTests(TestCase):
    def test_archive_includes_scripts_and_filters(self):
        from django.contrib.staticfiles import finders
        response = self.client.get(reverse('archive'))
        self.assertContains(response, '/static/js/helloworld.js')
        self.assertContains(response, '/static/js/fold-post.js')
        self.assertContains(response, 'id="group-form"')
        self.assertContains(response, 'id="average-form"')
        self.assertIsNotNone(finders.find('js/helloworld.js'))
        self.assertIsNotNone(finders.find('js/fold-post.js'))

    def test_each_article_has_fold_button(self):
        user = User.objects.create_user(username='reader')
        Article.objects.create(title='Первая', author=user, text='Первый текст')
        Article.objects.create(title='Вторая', author=user, text='Второй текст')
        response = self.client.get(reverse('archive'))
        self.assertContains(response, 'class="fold-button"', count=2)
