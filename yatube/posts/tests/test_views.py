from math import ceil

from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..forms import PostForm
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
        cls.index_url = ('posts:index', None, 'posts/index.html')
        cls.group_url = (
            'posts:group_list',
            (cls.group.slug,),
            'posts/group_list.html'
        )
        cls.profile_url = (
            'posts:profile',
            (cls.post.author,),
            'posts/profile.html'
        )
        cls.post_detail_url = (
            'posts:post_detail',
            (cls.post.pk,),
            'posts/post_detail.html'
        )
        cls.post_edit_url = (
            'posts:post_edit',
            (cls.post.pk,),
            'posts/create_post.html'
        )
        cls.create_post_url = (
            'posts:post_create',
            None,
            'posts/create_post.html'
        )
        cls.urls_all = (
            cls.index_url,
            cls.group_url,
            cls.profile_url,
            cls.post_detail_url,
            cls.post_edit_url,
            cls.create_post_url
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_all_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url_name, args, template in self.urls_all:
            with self.subTest(url_name=template):
                response = self.authorized_client.get(
                    reverse(url_name, args=args)
                )
                self.assertTemplateUsed(response, template)

    def custom_checking_func(self, first_object):
        self.assertEqual(first_object.author.username, self.user.username)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.group)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        name, _, _ = self.index_url
        response = self.authorized_client.get(reverse(name))
        self.assertIn('page_obj', response.context, msg='присутствует')
        self.assertGreaterEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.custom_checking_func(first_object)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        name, args, _ = self.group_url
        response = self.authorized_client.get(reverse(name, args=args))
        self.assertIn('page_obj', response.context, msg='присутствует')
        self.assertGreaterEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.custom_checking_func(first_object)
        self.assertEqual(
            response.context.get('group'), self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        name, args, _ = self.profile_url
        response = self.authorized_client.get(reverse(name, args=args))
        self.assertIn('page_obj', response.context, msg='присутствует')
        self.assertGreaterEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.custom_checking_func(first_object)
        self.assertEqual(
            response.context.get('author'), self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        name, args, _ = self.post_detail_url
        response = self.authorized_client.get(reverse(name, args=args))
        first_object = response.context['post']
        self.custom_checking_func(first_object)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        name, args, _ = self.create_post_url
        response = self.authorized_client.get(reverse(name, args=args))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        name, args, _ = self.post_edit_url
        response = self.authorized_client.get(reverse(name, args=args))
        self.assertTrue(response.context.get('is_edit'))
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('form').instance, self.post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='noname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.ALL_POSTS = 13
        Post.objects.bulk_create(
            [Post(author=cls.user, text=f"Тестовый пост {i}", group=cls.group)
                for i in range(cls.ALL_POSTS)]
        )

    def setUp(self):
        self.guest_client = Client()
        self.pagin_urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )

    def test_first_page_contains_ten_records(self):
        """Проверка пагинатора. 10 записей на первой странице"""
        for url in self.pagin_urls:
            response = self.guest_client.get(url)
            self.assertEqual(
                len(response.context['page_obj']),
                settings.POSTS_PER_PAGE
            )

    def test_second_page_contains_three_records(self):
        """Проверка пагинатора. 3 записи на второй странице"""
        page_number = ceil(self.ALL_POSTS / settings.POSTS_PER_PAGE)
        for url in self.pagin_urls:
            response = self.guest_client.get(
                url + '?page=' + str(page_number)
            )
            self.assertEqual(
                len(response.context['page_obj']),
                (self.ALL_POSTS - (
                    page_number - 1
                ) * settings.POSTS_PER_PAGE)
            )
