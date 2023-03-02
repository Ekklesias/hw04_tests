from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Post, Group


User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_of_post = User.objects.create_user(username="TestAuthor")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.author_of_post,
            group=cls.group
        )

    def setUp(self):
        # Создадим клиент и авторизуем автора поста
        self.client_for_author_of_post = Client()
        self.client_for_author_of_post.force_login(self.author_of_post)

    def test_create_new_post(self):
        # Подсчитаем количество записей в Post
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Заголовок из формы',
            'group': self.group.pk,
        }
        response = self.client_for_author_of_post.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Убедимся, что запись в базе данных создалась
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, 200)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.author_of_post})
        )
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group,
                author=PostCreateFormTests.author_of_post,
                text=form_data['text']
            ).exists()
        )

    def test_authorized_edit_post(self):
        """Проверяем, что автор может редактировать пост"""
        post_edit = Post.objects.get(id=self.post.id)
        form_data = {
            'text': 'Вот мы изменили пост',
            'group': self.group.pk
        }
        response_edit = self.client_for_author_of_post.post(
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': post_edit.pk
                    }),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(id=self.post.id)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, 'Вот мы изменили пост')
        self.assertEqual(post_edit.group, self.group)
