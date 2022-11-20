from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post, User


class PostViewsTests(TestCase):
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
            group=cls.group,
            author=cls.user,
            text='Тестовый пост',
        )
        cls.templates_page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'slug_slug'}),
            reverse('posts:profile', kwargs={'username': cls.user}),
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}),
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}),
            reverse('posts:post_create')
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': 'slug_slug'})
            ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
            ): 'posts/post_detail.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_group_profile_page_show_correct_cont(self):
        """Проверка контекста страниц index, group, profile"""
        context = [
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(reverse(
                'posts:group_list', kwargs={'slug': self.group.slug})),
            self.authorized_client.get(reverse(
                'posts:profile', kwargs={'username': self.user})),
        ]
        for response in context:
            self.assertTrue(response.context['page_obj'])
            first_object = response.context['page_obj'][0]
            context_objects = {
                self.user.id: first_object.author.id,
                self.post.text: first_object.text,
                self.group.slug: first_object.group.slug,
                self.post.id: first_object.id,
            }
            for reverse_name, response_name in context_objects.items():
                with self.subTest(reverse_name=reverse_name):
                    self.assertEqual(response_name, reverse_name)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})))
        first_object = response.context['post']
        self.assertEqual(first_object.pk, self.post.pk)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_create')))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([Post(
            author=cls.user,
            text=f'Тестовый пост {i}',
            group=cls.group)
            for i in range(13)])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def _test_pagination(self, url_params, expected_count):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index') + url_params,
            'posts/group_list.html':
                (reverse('posts:group_list', kwargs={'slug': self.group.slug}
                        ) + url_params),
            'posts/profile.html':
                (reverse('posts:profile', kwargs={'username': self.user}
                        ) + url_params),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), expected_count
                )

    def test_first_page_contains_ten_records(self):
        self._test_pagination('', settings.POSTS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        self._test_pagination('?page=2', settings.POSTS_ON_SECOND_PAGE)

    def test_first_page_group_list_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'slug_slug'}))
        self.assertEqual(len(response.context['page_obj']),
            settings.POSTS_PER_PAGE)

    def test_first_page_profile_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}))
        self.assertEqual(len(response.context['page_obj']),
            settings.POSTS_PER_PAGE)
