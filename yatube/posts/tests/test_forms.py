from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

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
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='slug_slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.urls = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': 'slug_slug'})
            ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': cls.user}):
            'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': cls.post.id})
            ): 'posts/post_detail.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': cls.post.id})
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма на странице create создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост1',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            self.urls,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_create = Post.objects.latest('id')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_create.text, form_data['text'])
        self.assertEqual(post_create.author, self.user)
        self.assertEqual(post_create.group.id, form_data['group'])

    def test_create_post_by_anonymous(self):
        """Форма поста, заполненнная не авторизованным клиентом
         на странице create, не создает запись в Post.
         """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост гостя',
            'group': self.group.id,
        }
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(text=form_data['text']).exists()
        )

    def test_post_edit_by_anonymous(self):
        """Форма поста, заполненнная не авторизованным клиентом
        на странице post_edit, не меняет значение полей поста.
        """
        form_data = {
            'text': 'Редактирование поста анонимом',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        self.assertNotEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])

    def test_post_edit_by_not_author(self):
        """Форма поста, заполненнная не автором
        на странице post_edit, не меняет значение полей поста.
        """
        author = User.objects.create_user(username='smbd')
        group = Group.objects.create(
            title='Тестовая группа2',
            slug='slug_slug3',
            description='Тестовое описание3',
        )
        post1 = Post.objects.create(
            author=author,
            text='abc',
            group=group
        )
        form_data = {
            'text': 'Редактирование поста',
            'group': self.group.id,
            'author': self.user
        }
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post1.id}),
            data=form_data,
            follow=True
        )
        post1.refresh_from_db()
        self.assertRedirects(
            response, f'/posts/{post1.id}/'
        )
        self.assertNotEqual(post1.text, form_data['text'])
        self.assertNotEqual(post1.group.id, form_data['group'])
        self.assertNotEqual(post1.author, form_data['author'])
