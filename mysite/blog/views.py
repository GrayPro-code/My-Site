from django.shortcuts import render, get_object_or_404
from .models import Post
from django.core.paginator import Paginator, EmptyPage
from django.views.generic import ListView


class PostListView(ListView):
    """    Альтернативное представление списка постов    """
    queryset = Post.published.all() # model=Post можно было бы и так, но у нас есть свой менеджер запросов

    context_object_name = 'posts'   # Если не указано имя контекстного объекта context_object_name,
                                    # то по умолчанию используется переменная object_list

    paginate_by = 3                 # в атрибуте paginate_by задается постраничная разбивка результатов
                                    # с возвратом трех объектов на страницу

    template_name = 'blog/post/list.html' # Если шаблон не задан, то по умолчанию List-View
                                          # будет использовать blog/post_list.html.


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    return render(request, 'blog/post/detail.html', {'post': post})


# если делать представление через функцию
#def post_list(request):
#    post_list = Post.published.all()
#    # Постраничная разбивка с 3 постами на страницу
#    paginator = Paginator(post_list, 3)
#    page_number = request.GET.get('page', 1)
#    try:
#        posts = paginator.get_page(page_number)
#    except EmptyPage:
#    # Если page_number находится вне диапазона, то выдать последнюю страницу
#        posts = paginator.page(paginator.num_pages)
#    return render(request,'blog/post/list.html',{'posts': posts})
#