from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='notauth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый пост',
        )
        cls.index_url = (
            '/',
            'posts/index.html',
            None
        )
        cls.group_url = (
            f'/group/{cls.group.slug}/',
            'posts/group_list.html',
            None
        )
        cls.profile_url = (
            f'/profile/{cls.user1.username}/',
            'posts/profile.html',
            None
        )
        cls.post_detail_url = (
            f'/posts/{cls.post.id}/',
            'posts/post_detail.html',
            None
        )
        cls.post_edit_url = (
            f'/posts/{cls.post.id}/edit/',
            'posts/create_post.html',
            '/auth/login/?next=/posts/1/edit/'
        )
        cls.create_post_url = (
            '/create/',
            'posts/create_post.html',
            '/auth/login/?next=/create/'
        )
        cls.urls_any = (
            cls.index_url,
            cls.group_url,
            cls.profile_url,
            cls.post_detail_url
        )
        cls.urls_logged = (
            cls.post_edit_url,
            cls.create_post_url
        )
        cls.urls_all = cls.urls_any + cls.urls_logged

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUrlsTest.user1)

    def test_urls_any_exists_at_desired_location_ok(self):
        """Страницы доступные любому пользователю."""
        for url, _, _ in self.urls_any:
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_logged_guest_found(self):
        """Страницы недоступные без авторизации."""
        for url, _, _ in self.urls_logged:
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_logged_guest_redirect(self):
        """Перенаправление гостей на страницу логина."""
        for url, _, adress in self.urls_logged:
            with self.subTest(url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, adress)

    def test_urls_logged_found(self):
        """Приватные cтраницы доступные авторизованным юзерам."""
        for url, _, _ in self.urls_logged:
            with self.subTest(url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url(self):
        """Страница редактирования поста доступна только автору."""
        self.user1 = User.objects.get(username=self.user1)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_redirect(self):
        """Редактирование поста не автором"""
        self.authorized_client.force_login(self.user2)
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    )
        )

    def unexisting_page(self):
        """Несуществующая страница."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template, _ in self.urls_all:
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
