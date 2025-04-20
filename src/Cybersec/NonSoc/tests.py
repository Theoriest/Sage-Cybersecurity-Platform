from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from user.models import NonSOCUser
from NonSoc.models import SecurityRequest, SecurityAwareness

User = get_user_model()

class NonSocTests(TestCase):
    def setUp(self):
        # Create a Non-SOC user
        self.non_soc_user = User.objects.create_user(
            username='non_soc_tester',
            email='non_soc@example.com',
            first_name='Non',
            last_name='SOC',
            password='nonsocpassword',
            user_type='non_soc'
        )
        self.non_soc_profile = NonSOCUser.objects.create(
            user=self.non_soc_user, 
            department='Marketing'
        )
        
        # Create a security request for testing
        self.security_request = SecurityRequest.objects.create(
            title='Access Request',
            description='Need access to secure system',
            status='pending',
            requester=self.non_soc_user
        )

    def test_create_security_request(self):
        self.client.login(username='non_soc_tester', password='nonsocpassword')
        response = self.client.post(reverse('non_soc:create_security_request'), {
            'title': 'New Security Request',
            'description': 'Request for security assessment',
            'priority': 'medium',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(SecurityRequest.objects.filter(title='New Security Request').exists())
    
    def test_security_request_detail(self):
        self.client.login(username='non_soc_tester', password='nonsocpassword')
        response = self.client.get(reverse('non_soc:security_request_detail', args=[self.security_request.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Access Request')
    
    def test_complete_security_awareness(self):
        self.client.login(username='non_soc_tester', password='nonsocpassword')
        awareness = SecurityAwareness.objects.create(
            title='Phishing Awareness',
            content='Learn to identify phishing emails',
            points=10
        )
        response = self.client.post(reverse('non_soc:complete_awareness', args=[awareness.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after completion
        
        # Check if user has this awareness completed
        user_awareness = self.non_soc_user.completed_awareness.all()
        self.assertIn(awareness, user_awareness)
    
    def test_non_soc_dashboard_access(self):
        self.client.login(username='non_soc_tester', password='nonsocpassword')
        response = self.client.get(reverse('non_soc:dashboard'))
        self.assertEqual(response.status_code, 200)
