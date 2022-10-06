from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, User, Follow
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from .utils import page_list
from django.core.cache import cache


TITLE_LEN: int = 30
CACHE_CLEAR_TIME: int = 20


def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = page_list(post_list, request)
    context = {
        'page_obj': page_obj,
    }
    if not cache.get('index_page'):
        cache.set('index_page', context, CACHE_CLEAR_TIME)
    else:
        context = cache.get('index_page')
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date')
    page_obj = page_list(post_list, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    post_list = author.posts.all().order_by('-pub_date')
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    page_obj = page_list(post_list, request)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    title = f'Пост {post.text[:TITLE_LEN]}'
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'title': title,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    is_edit = False
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None
    )
    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post,
    }
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.pk)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user).values('author')
    posts = Post.objects.filter(author__in=follow)
    page_obj = page_list(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user != get_object_or_404(User, username=username):
        Follow.objects.get_or_create(
            user=request.user,
			author=User.objects.get(username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author=User.objects.get(username=username)
    ).delete()
    return redirect('posts:profile', request.user)
