from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # представления поста
    # path('', views.post_list, name='post_list'), # через функцию
    path('', views.PostListView.as_view(), name='post_list'), # через класс
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    ]

