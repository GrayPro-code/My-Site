from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count

from django.contrib.postgres.search import SearchVector, SearchQuery, TrigramSimilarity

# если делать представление через функцию
def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    # Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.get_page(page_number)
    except EmptyPage:
    # Если page_number находится вне диапазона, то выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)
    return render(request,'blog/post/list.html',{'posts': posts,
                                                                    'tag': tag })

#class PostListView(ListView):
#    """    Альтернативное представление списка постов    """
#    queryset = Post.published.all() # model=Post можно было бы и так, но у нас есть свой менеджер запросов
#
#    context_object_name = 'posts'   # Если не указано имя контекстного объекта context_object_name,
#                                    # то по умолчанию используется переменная object_list
#
#    paginate_by = 3                 # в атрибуте paginate_by задается постраничная разбивка результатов
#                                    # с возвратом трех объектов на страницу
#
#    template_name = 'blog/post/list.html' # Если шаблон не задан, то по умолчанию List-View
#                                          # будет использовать blog/post_list.html.


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)
    # Форма для комментирования пользователями
    form = CommentForm()

    # Список схожих постов
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids) \
        .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')) \
        .order_by('-same_tags', '-publish')[:4]

    return render(request, 'blog/post/detail.html', {'post': post,
                                                                        'comments': comments,
                                                                        'form': form,
                                                                        'similar_posts': similar_posts})

def post_share(request, post_id):
    # Извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'gray.aloner@gmail.com',
                      [cd['to']])
            sent = True
    else:
        form = EmailPostForm()

    return render(request, 'blog/post/share.html', {'post': post,
                                                                        'form': form,
                                                                        'sent': sent})

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, \
                                   status=Post.Status.PUBLISHED)
    comment = None
    # A comment was posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Create a Comment object without saving it to the database
        comment = form.save(commit=False)
        # Assign the post to the comment
        comment.post = post
        # Save the comment to the database
        comment.save()
    return render(request, 'blog/post/comment.html',
                           {'post': post,
                            'form': form,
                            'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            # Prepared for weighted search across title and body.
            search_vector = (
                SearchVector('title', weight='A', config='english')
                + SearchVector('body', weight='B', config='english')
            )
            search_query = SearchQuery(query, config='english')
            # Actual similarity calculation (original behavior): title-only trigram similarity.
            results = (
                Post.published.annotate(
                    similarity=TrigramSimilarity('title', query),
                )
                .filter(similarity__gt=0.1)
                .order_by('-similarity')
            )

    return render(
        request,
        'blog/post/search.html',
        {
            'form': form,
            'query': query,
            'results': results,
        },
    )
