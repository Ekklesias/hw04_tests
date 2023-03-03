from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.conf import settings

from posts.forms import PostForm
from posts.models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClass()
        cls.author_of_post = User.objects.create_user(username="TestAuthor")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы'
        )
        # Создадим вторую группу для проверки, куда попал пост
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-group2',
            description='Тестовое описание группы2'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author_of_post,
            group=cls.group
        )

    def setUp(self):
        self.user_auth = User.objects.create_user(username='AuthUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_auth)
        self.client_for_author_of_post = Client()
        self.client_for_author_of_post.force_login(self.author_of_post)

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""
        with self.subTest(post=post):
            self.assertEqual(post.id, self.post.id)
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test-group'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'TestAuthor'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': '1'})
            ),
            'posts/create.html': reverse('posts:post_create')
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.client_for_author_of_post.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index с правильным контекстом"""
        response = self.client_for_author_of_post.get(reverse('posts:index'))
        self.posts_check_all_fields(response.context['page_obj'][0])
        self.assertIn('page_obj', response.context)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list с правильным контекстом"""
        response = (self.client_for_author_of_post.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})))
        self.posts_check_all_fields(response.context['page_obj'][0])
        self.assertIn('page_obj', response.context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile с правильным контекстом"""
        response = (self.client_for_author_of_post.get(
            reverse('posts:profile',
                    kwargs={'username': self.author_of_post.username})))
        self.posts_check_all_fields(response.context['page_obj'][0])
        self.assertIn('page_obj', response.context)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail с правильным контекстом"""
        response = (self.client_for_author_of_post.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'})))
        self.posts_check_all_fields(response.context['post'])

    def test_create_page_show_correct_context(self):
        """Проверка форм создания и редактирования поста - create."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ChoiceField,
        }
        urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.pk,)),
        )
        for url, slug in urls:
            reverse_name = reverse(url, args=slug)
            with self.subTest(reverse_name=reverse_name):
                response = self.client_for_author_of_post.get(reverse_name)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_post_on_index_group_profile_create(self):
        """Созданный пост появился в Группе, Профайле, Главной"""
        reverse_page_names_post = {
            reverse('posts:index'): self.group.slug,
            reverse('posts:profile', kwargs={
                'username': self.author_of_post}): self.group.slug,
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): self.group.slug,
        }
        for value, expected in reverse_page_names_post.items():
            response = self.authorized_client.get(value)
            for object in response.context['page_obj']:
                post_group = object.group.slug
                with self.subTest(value=value):
                    self.assertEqual(post_group, expected)

    def test_post_not_in_other_group(self):
        """Пост не появился в другой группе"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group2.slug}
            )
        )
        self.assertNotIn(self.post, response.context.get('page_obj'))
        group2 = response.context.get('group')
        self.assertNotEqual(group2, self.group)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_of_post2 = User.objects.create_user(username="TestAuthor2")
        # Создадим запись в БД для группы
        cls.group = Group.objects.create(
            title='Group for Paginator',
            slug='paginat',
            description='For test of paginator',
        )
        for test_post in range(1, 14):
            Post.objects.create(
                text=f'Text {test_post}',
                author=cls.author_of_post2,
                group=cls.group
            )

    def setUp(self):
        self.client_for_author_of_post = Client()
        self.client_for_author_of_post.force_login(self.author_of_post2)

    def test_first_page_contains_ten_records(self):
        response = self.client_for_author_of_post.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_AMOUNT
        )

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        all_posts = Post.objects.count()
        response = self.client_for_author_of_post.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            all_posts - settings.POSTS_AMOUNT
        )

    def test_page_contains_ten_and_3_posts(self):
        paginator_urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author_of_post2.username,))
        )
        count_posts = (
            ('?page=1', settings.POSTS_AMOUNT),
            ('?page=2', settings.POSTS_AMOUNT2)
        )
        for address, args in paginator_urls:
            for page, count in count_posts:
                with self.subTest(page=page):
                    response = self.client_for_author_of_post.get(
                        reverse(address, args=args) + page
                    )
                    self.assertEqual(len(response.context['page_obj']), count)
