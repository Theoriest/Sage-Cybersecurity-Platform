from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Incident, IncidentResponse

User = get_user_model()

class SocTests(TestCase):
    def setUp(self):
        # Create a SOC user
        self.soc_user = User.objects.create_user(
            username='soc_tester',
            email='soc_test@example.com',
            first_name='SOC',
            last_name='Tester',
            password='socpassword123',
            user_type='soc'
        )
        self.soc_profile = SOCUser.objects.create(
            user=self.soc_user, 
            unique_identifier='SOC123', 
            role='analyst'
        )
        
        # Create an incident for testing
        self.incident = Incident.objects.create(
            title='Test Security Breach',
            description='This is a test security incident',
            severity='high',
            status='open',
            reporter=self.soc_user
        )

    def test_create_incident(self):
        self.client.login(username='soc_tester', password='socpassword123')
        response = self.client.post(reverse('soc:create_incident'), {
            'title': 'New Security Incident',
            'description': 'Description of new incident',
            'severity': 'medium',
            'status': 'open',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Incident.objects.filter(title='New Security Incident').exists())
    
    def test_incident_detail(self):
        self.client.login(username='soc_tester', password='socpassword123')
        response = self.client.get(reverse('soc:incident_detail', kwargs={'pk': self.incident.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Security Breach')
    
    def test_add_incident_response(self):
        self.client.login(username='soc_tester', password='socpassword123')
        response = self.client.post(reverse('soc:add_incident_response', kwargs={'pk': self.incident.id}), {
            'content': 'This is a test response to the incident',
            'action_taken': 'Investigated source IP',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after adding response
        self.assertTrue(IncidentResponse.objects.filter(incident=self.incident).exists())
    
    def test_soc_dashboard_access(self):
        self.client.login(username='soc_tester', password='socpassword123')
        response = self.client.get(reverse('soc:dashboard'))
        self.assertEqual(response.status_code, 200)
