from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.text import slugify
from .models import Article, Category, Comment
from .forms import ArticleForm, CommentForm

@login_required
def write_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.status = 'published'  # Ensure it's published
            article.save()
            form.save_m2m()  # Save many-to-many relationships (categories)
            
            # Redirect to appropriate dashboard instead of trying to use read_article
            if request.user.user_type == 'soc':
                return redirect('soc:dashboard')
            else:
                return redirect('non_soc:dashboard')
    else:
        form = ArticleForm()
    return render(request, 'write_article.html', {'form': form})

@login_required
def read_article(request, article_id):
    article = Article.objects.get(id=article_id)
    return render(request, 'read_article.html', {'article': article})

@login_required
def article_list(request):
    articles = Article.objects.filter(status='published').order_by('-created_at')
    categories = Category.objects.all()
    
    context = {
        'articles': articles,
        'categories': categories
    }
    return render(request, 'article_list.html', context)

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')
    comments = article.comments.all().order_by('-created_at')
    
    context = {
        'article': article,
        'comments': comments
    }
    return render(request, 'articles/article_detail.html', context)

def article_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    articles = Article.objects.filter(categories=category, status='published').order_by('-created_at')
    
    context = {
        'category': category,
        'articles': articles
    }
    return render(request, 'articles/article_category.html', context)

@login_required
def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            # Handle many-to-many relationship manually after saving the form
            form.save_m2m()
            return redirect('article_detail', slug=article.slug)
    else:
        form = ArticleForm()
    
    return render(request, 'articles/create_article.html', {'form': form})

@login_required
def add_comment(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
            return redirect('article_detail', slug=article.slug)
    else:
        form = CommentForm()
    
    return render(request, 'articles/add_comment.html', {'form': form, 'article': article})

def article_search(request):
    query = request.GET.get('q', '')
    if query:
        articles = Article.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query),
            status='published'
        ).order_by('-created_at')
    else:
        articles = Article.objects.none()
    
    context = {
        'articles': articles,
        'query': query
    }
    return render(request, 'articles/article_search.html', context)

@login_required
@require_POST
def add_category(request):
    """Add a new category and return it as JSON"""
    if request.user.user_type != 'soc':
        return JsonResponse({'success': False, 'error': 'Only SOC users can create categories'}, status=403)
        
    category_name = request.POST.get('category_name', '').strip()
    if not category_name:
        return JsonResponse({'success': False, 'error': 'Category name is required'}, status=400)
    
    # Check if category already exists
    if Category.objects.filter(name__iexact=category_name).exists():
        existing_category = Category.objects.get(name__iexact=category_name)
        return JsonResponse({
            'success': True, 
            'category_id': existing_category.id,
            'category_name': existing_category.name,
            'message': 'Category already exists'
        })
    
    # Create new category
    category = Category(name=category_name)
    category.slug = slugify(category_name)
    category.save()
    
    # Return JSON response for AJAX or redirect for normal form submission
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'category_id': category.id,
            'category_name': category.name
        })
    else:
        messages.success(request, f'Category "{category_name}" has been created')
        return redirect(request.POST.get('next', 'articles:write_article'))
