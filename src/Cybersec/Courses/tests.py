from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from Courses.models import Course, Module, Enrollment, CompletedModule

User = get_user_model()

class CoursesTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='course_tester',
            email='course@example.com',
            password='coursepassword',
            first_name='Test',  # Added the required arguments
            last_name='User'    # Added the required arguments
        )
        
        # Create a course and modules
        self.course = Course.objects.create(
            title='Security Awareness 101',
            description='Basic security awareness training',
            difficulty_level='beginner',
            created_by=self.user  # Added the missing required field
        )
        
        self.module1 = Module.objects.create(
            course=self.course,
            title='Password Safety',
            content='Creating strong passwords is essential...',
            order=1
        )
        
        self.module2 = Module.objects.create(
            course=self.course,
            title='Phishing Prevention',
            content='How to identify and avoid phishing attempts...',
            order=2
        )

    def test_course_listing(self):
        self.client.login(username='course_tester', password='coursepassword')
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Security Awareness 101')
    
    def test_course_detail(self):
        self.client.login(username='course_tester', password='coursepassword')
        response = self.client.get(reverse('course_detail', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Security Awareness 101')
        self.assertContains(response, 'Password Safety')
        self.assertContains(response, 'Phishing Prevention')
    
    def test_module_detail(self):
        self.client.login(username='course_tester', password='coursepassword')
        # First enroll in the course
        Enrollment.objects.create(user=self.user, course=self.course)
        
        response = self.client.get(reverse('module_detail', args=[self.module1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password Safety')
    
    def test_course_enrollment(self):
        self.client.login(username='course_tester', password='coursepassword')
        response = self.client.post(reverse('enroll_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after enrollment
        self.assertTrue(Enrollment.objects.filter(user=self.user, course=self.course).exists())
    
    def test_complete_module(self):
        self.client.login(username='course_tester', password='coursepassword')
        # Enroll in course first
        Enrollment.objects.create(user=self.user, course=self.course)
        
        response = self.client.post(reverse('complete_module', args=[self.module1.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after completion
        self.assertTrue(CompletedModule.objects.filter(user=self.user, module=self.module1).exists())
        
        # Check course progress
        enrollment = Enrollment.objects.get(user=self.user, course=self.course)
        self.assertEqual(enrollment.progress, 50)  # 1/2 modules completed = 50%
