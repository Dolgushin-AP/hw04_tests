from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostUrlsTest(TestCase):
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
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUrlsTest.user)

    def guest_client_urls(self):
        """Страницы доступные любому пользователю."""
        url_names = (
            '/',
            '/group/slug_slug/',
            '/profile/auth/',
            '/posts/1/',
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                access_error = f'address{address}, no access'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    access_error
                )

    def test_post_create_url(self):
        """Страница create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url(self):
        author = User.objects.create_user(username='test')
        post = Post.objects.create(
            author=author,
            text='text',
            group=self.group
        )
        self.authorized_client.force_login(author)
        response = self.authorized_client.get(f'/posts/{post.id}/edit/')
        self.assertEquals(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница posts/<int:post_id>/edit/ перенаправляет анонима."""
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/edit/'))

    def test_post_create_url_redirect_anonymous(self):
        """Страница create/ перенаправляет анонима."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def unexisting_page(self):
        """Несуществующая страница."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/slug_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
