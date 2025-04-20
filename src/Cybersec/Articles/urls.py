from django.urls import path
from . import views

app_name = 'articles'  # This creates the articles namespace

urlpatterns = [
    path('write/', views.write_article, name='write_article'),
    path('read/<int:article_id>/', views.read_article, name='read_article'),
    path('list/', views.article_list, name='article_list'),
    path('comment/<int:article_id>/', views.add_comment, name='add_comment'),
    path('search/', views.article_search, name='article_search'),
    path('category/add/', views.add_category, name='add_category'),
]