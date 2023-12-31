from __future__ import annotations
import typing

from django.conf import settings
from django.db import models
from django import forms
from django.core.handlers.wsgi import WSGIRequest
from rest_framework.request import Request
from tinymce.models import HTMLField

from sapp.models import SM, AbstractUser, ImageField


class Category(SM):
    icon = "fas fa-ad"
    list_field_names = ("id", "name", "image")
    serializer_list_field_names = list_field_names + ("header", )
    detail_field_names = ("id", "name", "image", "header") + SM.sm_meta_field_names
    api_methods = ("get_category_post_stats_api", "get_category_author_stats_api")
    queryset_names = ("posts",)

    class Meta(SM.Meta):
        verbose_name_plural = "Categories"

    name = models.CharField(max_length=256)
    image = ImageField(upload_to="blog_posts")
    header = models.TextField(blank=True, null=True, max_length=256)

    @property
    def posts(self):
        return Post.objects.filter(category = self)
    
    @classmethod
    def get_category_post_stats_api(cls, request: Request, kwds: dict):
        return cls.get_category_post_stats()

    @classmethod
    def get_category_post_stats(cls):
        data = {}
        for i in Category.objects.all():
            data[f"{i.name}"] = Post.objects.filter(category_id=i.pk).count()
        return data
    
    @classmethod
    def get_category_author_stats_api(cls, request: Request, kwds: dict):
        return cls.get_category_author_stats()

    @classmethod
    def get_category_author_stats(cls):
        data = {}
        for i in Category.objects.all():
            data[f"{i.name}"] = Author.objects.filter(categories__in=[i]).count()
        return data
    
    def __str__(self):
        return self.name


class Author(SM):
    icon = "fas fa-user-tie"
    list_field_names = ("id", "user", "image", "full_name")
    queryset_names = ("posts", )
    api_methods = ("get_author_ctx_api", )

    user: models.OneToOneField[AbstractUser] = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    full_name = models.CharField(max_length=256)
    image = ImageField(upload_to="blog_authors", blank=True, null=True)
    about = HTMLField()
    categories = models.ManyToManyField(Category, blank=True)

    def __str__(self):
        return self.full_name

    @property
    def posts(self):
        return Post.objects.filter(author = self)
    
    @classmethod
    def get_author_ctx_api(cls, request: Request, kwds: dict):
        author = Author.objects.filter(user=request.user).first()
        if not author:
            return None
        serializer_class = cls.get_serializer(request, ("id", "full_name", "user", "image", "about", "categories"))
        return serializer_class(instance=author).data


class Post(SM):
    icon = "fas fa-blog"
    list_field_names = ("id", "title", "image", "category", "author", "published", "reads", "creation_timestamp")
    serializer_list_field_names = list_field_names + ("serialized_author", "serialized_category")
    detail_field_names = list_field_names + ("body", "keywords") + SM.sm_meta_field_names
    serializer_detail_field_names = tuple(set(serializer_list_field_names+ detail_field_names))
    filter_field_names = ("author", "published", "category", "created_by")
    queryset_names = ("comments",)
    
    has_attachments = True
    has_reactions = True
    confirm_delete = True
    has_bookmarks = True

    title = models.CharField(max_length=256)
    image = ImageField(upload_to="blog_posts")
    body = HTMLField()
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, blank=True, null=True)
    published = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    keywords = models.CharField(max_length=256, blank=True, null=True)
    reads = models.PositiveIntegerField(default=0, blank=True)

    @property
    def comments(self):
        return Comment.objects.filter(post_id=self.pk)
    
    @property
    def serialized_author(self):
        return self.author.values_dict("id", "full_name") if self.author else None
    
    @property
    def serialized_category(self):
        return self.category.values_dict("id", "name")

    def set_published(self):
        if not self.updated_by.has_perm("blog.publish_post"):
            self.published = False
    
    def set_author(self):
        if not self.author:
            self.author = self.created_by

    def save(self, *args, **kwargs):
        self.set_published()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

    @classmethod
    def get_filters_form(cls, request: WSGIRequest, _fields: typing.Iterable=None):
        super_form = super().get_filters_form(request, _fields)
        class FilterForm(super_form):
            title__icontains = forms.CharField(label="Title")
            keywords__icontains = forms.CharField(label="Keywords")
            body__icontains = forms.CharField(label="Body")
            id__in = forms.MultipleChoiceField(label="ID In", choices=cls.objects.values_list("id", "id"))
        return FilterForm


class Comment(SM):
    class Meta(SM.Meta):
        ordering = ("-id", )
    icon = "fas fa-comment-dots"
    list_field_names = ("id", "post", "text", "created_by", "username", "creation_timestamp")
    filter_field_names = ("post",)

    text = models.TextField(max_length=512)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_comments")
    comment = models.ForeignKey("self", on_delete=models.CASCADE, related_name="comment_comments", blank=True, null=True)
    username = models.CharField(max_length=256, blank=True)

    @property
    def replies(self):
        return Comment.objects.filter(comment__id=self.id)
    
    @property
    def list_url(self):
        return self.post.detail_url
    
    def set_username(self):
        self.username = str(self.updated_by or self.created_by)
    
    def save(self, *args, **kwargs):
        self.set_username()
        return super().save(*args, **kwargs)


class Following(SM):
    class Meta(SM.Meta):
        unique_together = ("follower", "author")
    
    icon = "fas fa-grin-hearts"

    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.follower} follows {self.author}"