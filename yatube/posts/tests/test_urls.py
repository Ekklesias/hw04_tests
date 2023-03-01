from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим автора поста
        cls.author_of_post = User.objects.create_user(username="TestAuthor")
        # Создадим запись в БД для группы
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы'
        )
        # Создадим тестовый пост и присвоим автору
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author_of_post,
            group=cls.group
        )
        # Шаблоны по адресам
        cls.templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-group/': 'posts/group_list.html',
            '/profile/TestAuthor/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create.html',
            '/create/': 'posts/create.html',
        }
        # список со статусам кодов
        cls.temp_urls_status_code = {
            '/': HTTPStatus.OK,
            '/group/test-group/': HTTPStatus.OK,
            '/profile/TestAuthor/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
        }

    # Создадим программные клиенты
    def setUp(self):
        # клиент неавторизованного юзера
        self.guest_client = Client()
        # Создадим ещё одного пользователя
        self.user_auth = User.objects.create_user(username='TestAuth')
        # Создаём ещё один клиент и авторизовываем этого пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_auth)
        # Создадим клиент и авторизуем автора поста
        self.client_for_author_of_post = Client()
        self.client_for_author_of_post.force_login(self.author_of_post)

    def test_unexisting_page_correct_status(self):
        """Страница по адресу 'unexisting_page' вернёт ошибку 404."""
        response = self.guest_client.get('/unexisting_page/').status_code
        self.assertEqual(response, HTTPStatus.NOT_FOUND)

    def test_client_for_author_of_post_status_code(self):
        """Проверим, что все страницы доступны автору."""
        for address, status_code in self.temp_urls_status_code.items():
            if address != '/unexisting_page/':
                with self.subTest(address=address):
                    response = self.client_for_author_of_post.get(
                        address).status_code
                    self.assertEqual(response, status_code)

    def test_authorized_client_status_code(self):
        """Проверим, что все страницы доступны НЕавтору,
        кроме edit. C edit редирект на post_detail"""
        edit_url = '/posts/1/'
        for address, status_code in self.temp_urls_status_code.items():
            if address != '/posts/1/edit/':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address).status_code
                    self.assertEqual(response, status_code)
            else:
                response = self.authorized_client.get(address)
                self.assertRedirects(response, edit_url)

    def test_guest_client_status_code(self):
        """Проверим, что все страницы доступны анониму,
        кроме edit и create. C ними редирект на авторизацию"""
        auth_url = '/auth/login/?next='
        for address, status_code in self.temp_urls_status_code.items():
            if address != '/posts/1/edit/' and address != '/create/':
                with self.subTest(address=address):
                    response = self.guest_client.get(address).status_code
                    self.assertEqual(response, status_code)
            else:
                response = self.guest_client.get(address)
                self.assertRedirects(response, f'{auth_url}{address}')

    def test_urls_uses_correct_template1(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            if address != '/posts/1/edit/' and address != '/create/':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
            elif address == '/posts/1/edit/':
                response = self.client_for_author_of_post.get(address)
                self.assertTemplateUsed(response, template)
            else:
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
