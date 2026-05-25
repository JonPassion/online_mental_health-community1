from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count
from .models import Post, Comment, Reaction, REACTION_CHOICES
from .forms import PostForm


def post_list(request):
    posts = Post.objects.all().order_by('-created_at').annotate(
        comment_count=Count('comments', distinct=True),
        reaction_count=Count('reactions', distinct=True),
    )
    return render(request, 'posts/post_list.html', {'posts': posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.select_related('author').all()

    # Build reaction summary: {type: {emoji, count, reacted_by_me}}
    reaction_summary = []
    user_reaction = None
    if request.user.is_authenticated:
        user_reaction_obj = post.reactions.filter(user=request.user).first()
        user_reaction = user_reaction_obj.reaction_type if user_reaction_obj else None

    for rtype, emoji in REACTION_CHOICES:
        count = post.reactions.filter(reaction_type=rtype).count()
        reaction_summary.append({
            'type': rtype,
            'emoji': emoji,
            'count': count,
            'active': user_reaction == rtype,
        })

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'reaction_summary': reaction_summary,
        'user_reaction': user_reaction,
    })


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/post_create.html', {'form': form, 'post': post})


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment = Comment.objects.create(post=post, author=request.user, content=content)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': comment.id,
                    'author': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%b %d, %Y %H:%M'),
                })
    return redirect('posts:post_detail', pk=pk)


@login_required
def toggle_reaction(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    post = get_object_or_404(Post, pk=pk)
    reaction_type = request.POST.get('reaction_type')

    valid_types = [r[0] for r in REACTION_CHOICES]
    if reaction_type not in valid_types:
        return JsonResponse({'error': 'Invalid reaction type'}, status=400)

    existing = Reaction.objects.filter(post=post, user=request.user).first()

    if existing:
        if existing.reaction_type == reaction_type:
            # Same reaction — remove it (toggle off)
            existing.delete()
            user_reaction = None
        else:
            # Different reaction — switch it
            existing.reaction_type = reaction_type
            existing.save()
            user_reaction = reaction_type
    else:
        Reaction.objects.create(post=post, user=request.user, reaction_type=reaction_type)
        user_reaction = reaction_type

    # Return updated counts
    counts = {}
    for rtype, emoji in REACTION_CHOICES:
        counts[rtype] = post.reactions.filter(reaction_type=rtype).count()

    return JsonResponse({'user_reaction': user_reaction, 'counts': counts})
