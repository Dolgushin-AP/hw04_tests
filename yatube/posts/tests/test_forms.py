from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post
from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.post_edit_url = ('posts:post_edit', (cls.post.id,))
        cls.create_post_url = ('posts:post_create', None)
        cls.user_login_url = ('users:login', None)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый пост',
        }
        response = self.authorized_client.post(
            reverse(self.create_post_url[0]),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Тестовый пост',
                author=self.user,
            ).exists()
        )
        post_create = Post.objects.latest('id')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_create.text, form_data['text'])
        self.assertEqual(post_create.author, self.user)
        self.assertEqual(post_create.group.id, form_data['group'])

    def test_post_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.pk,
            'text': 'Тестовый пост',
        }
        name, args = self.post_edit_url
        response = self.authorized_client.post(
            reverse(name, args=args),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text='Тестовый пост',
                author=self.user,
            ).exists()
        )
        post_post_edit = Post.objects.latest('id')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_post_edit.text, form_data['text'])
        self.assertEqual(post_post_edit.author, self.user)
        self.assertEqual(post_post_edit.group.id, form_data['group'])

    def test_create_post(self):
        """Неавторизованный пользователь не отправит форму записи в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
        }
        name, args = self.create_post_url
        response = self.guest_client.post(
            reverse(name, args=args),
            data=form_data,
            follow=True,
        )
        create = reverse(name, args=args)
        name, args = self.user_login_url
        login = reverse(name, args=args)
        self.assertRedirects(response, f'{login}?next={create}')
        self.assertEqual(Post.objects.count(), posts_count)
