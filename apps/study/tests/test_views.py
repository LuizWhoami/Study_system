from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class StudySessionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='a', password='x')
        self.client = Client()
        self.client.force_login(self.user)

    def test_current_returns_inactive_when_none(self):
        r = self.client.get('/estudo/session/current/')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()['active'])

    def test_start_rejects_empty_payload(self):
        r = self.client.post('/estudo/start/', {})
        self.assertEqual(r.status_code, 400)

    def test_end_without_active_returns_404(self):
        r = self.client.post('/estudo/end/', {})
        self.assertEqual(r.status_code, 404)

    def test_pause_without_active_returns_404(self):
        r = self.client.post('/estudo/session/pause/')
        self.assertEqual(r.status_code, 404)

    def test_resume_without_active_returns_404(self):
        r = self.client.post('/estudo/session/resume/')
        self.assertEqual(r.status_code, 404)

    def test_anonymous_redirected(self):
        c = Client()
        r = c.get('/estudo/session/current/')
        self.assertEqual(r.status_code, 302)
