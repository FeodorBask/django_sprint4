from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Post, Category, Comment
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.db.models import Count


User = get_user_model()


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    now = timezone.now()
    is_owner = False
    if request.user.is_authenticated:
        is_owner = request.user.id == profile_user.id

    if is_owner:
        post_list = Post.objects.select_related(
            'category', 'location', 'author'
        ).filter(author=profile_user).order_by('-pub_date')
    else:
        post_list = Post.objects.select_related(
            'category', 'location', 'author'
        ).filter(
            author=profile_user,
            pub_date__lte=now,
            is_published=True,
            category__is_published=True
        ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile_user,
        'page_obj': page_obj,
        'now': now,
        'is_owner': is_owner
    }

    return render(request, 'blog/profile.html', context)


def index(request):
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {
        'page_obj': page_obj,
        'post_list': page_obj.object_list,
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        category=category,
        pub_date__lte=timezone.now(),
        is_published=True
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
        'post_list': page_obj.object_list,
    })


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=post_id,
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    )

    comments = post.comments.select_related('author').all()

    form = CommentForm()
    print(f"Form created: {form}")
    print(f"Form fields: {form.fields}")

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, 'blog/detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            if post.pub_date > timezone.now():
                messages.info(
                    request,
                    f'Пост будет опубликован '
                    f'{post.pub_date.strftime("%d.%m.%Y %H:%M")}'
                )

            messages.success(request, 'Пост успешно создан!')
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()

    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        messages.error(request, 'Вы не можете редактировать чужие публикации.')
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            request.FILES,
            instance=post,
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Пост успешно обновлён!')
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post, user=request.user)

    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        messages.error(request, 'Вы не можете удалять чужие публикации.')
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        if request.POST.get('confirm') == 'on':
            post.delete()
            messages.success(request, 'Пост успешно удалён!')
            return redirect('blog:profile', username=request.user.username)
        else:
            messages.error(request, 'Подтвердите удаление.')

    return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = Comment(
                text=form.cleaned_data['text'],
                post=post,
                author=request.user
            )
            comment.save()

            messages.success(request, 'Комментарий добавлен!')
            return redirect('blog:post_detail', post_id=post.id)
        else:
            messages.error(request, 'Ошибка при добавлении комментария')

    return redirect('blog:post_detail', post_id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        messages.error(
            request,
            'Вы не можете редактировать чужие комментарии.'
        )
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.is_edited = True
            comment.save()
            messages.success(request, 'Комментарий отредактирован!')
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        messages.error(request, 'Вы не можете удалять чужие комментарии.')
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        confirm = request.POST.get('confirm', False)

        if confirm:
            comment.delete()
            messages.success(request, 'Комментарий успешно удалён!')
            return redirect('blog:post_detail', post_id=post_id)
        else:
            messages.error(request, 'Подтвердите удаление, отметив чекбокс.')
            return render(request, 'blog/comment.html', {
                'comment': comment,
                'post': comment.post,
            })

    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post': comment.post,
    })


def csrf_failure(request, reason=""):
    return render(request, 'pages/403csrf.html',
                  {'reason': reason}, status=403)


def page_not_found(request, exception):
    return render(request, 'pages/404.html',
                  {'exception': exception}, status=404)


def server_error(request):
    return render(request, 'pages/500.html', status=500)


def permission_denied(request, exception):
    return render(request, 'pages/403csrf.html',
                  {'exception': exception}, status=403)
