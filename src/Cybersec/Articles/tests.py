from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from Articles.models import Article, Category, Comment

User = get_user_model()

class ArticlesTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='article_tester',
            email='article@example.com',
            password='articlepassword',
            user_type='soc',
            first_name='Test',  # Added the required arguments
            last_name='User'    # Added the required arguments
        )
        
        # Create category and article
        self.category = Category.objects.create(name='Security Best Practices')
        
        self.article = Article.objects.create(
            title='How to Secure Your Workstation',
            content='Detailed steps to secure your workstation...',
            author=self.user,
            status='published'
        )
        self.article.categories.add(self.category)

    def test_article_listing(self):
        response = self.client.get(reverse('article_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'How to Secure Your Workstation')
    
    def test_article_detail(self):
        response = self.client.get(reverse('article_detail', args=[self.article.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'How to Secure Your Workstation')
        self.assertContains(response, 'Detailed steps to secure your workstation')
    
    def test_article_category_filter(self):
        response = self.client.get(reverse('article_by_category', args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'How to Secure Your Workstation')
    
    def test_create_article(self):
        self.client.login(username='article_tester', password='articlepassword')
        response = self.client.post(reverse('create_article'), {
            'title': 'New Security Article',
            'content': 'Content of the new security article',
            'categories': [self.category.id],
            'status': 'published',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Article.objects.filter(title='New Security Article').exists())
    
    def test_add_comment(self):
        self.client.login(username='article_tester', password='articlepassword')
        response = self.client.post(reverse('add_comment', args=[self.article.id]), {
            'content': 'This is a test comment on the article',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after commenting
        self.assertTrue(Comment.objects.filter(article=self.article, user=self.user).exists())
    
    def test_article_search(self):
        # Create another article for search testing
        Article.objects.create(
            title='Encryption Basics',
            content='Understanding encryption fundamentals...',
            author=self.user,
            status='published'
        )
        
        response = self.client.get(reverse('article_search') + '?q=encryption')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Encryption Basics')
        self.assertNotContains(response, 'How to Secure Your Workstation')
