from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.study.models import StudySession
from apps.study import services
from apps.study.services import ActiveSessionExists, NoActiveSession

User = get_user_model()


class StudySessionServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='a', password='x')

    def test_start_creates_running_session(self):
        session = services.start_session(self.user, topic=None)
        self.assertEqual(session.status, StudySession.STATUS_RUNNING)
        self.assertEqual(session.user, self.user)
        self.assertIsNotNone(session.start_time)
        self.assertIsNone(session.end_time)

    def test_start_rejects_when_active_exists(self):
        services.start_session(self.user, topic=None)
        with self.assertRaises(ActiveSessionExists):
            services.start_session(self.user, topic=None)

    def test_only_one_active_per_user(self):
        services.start_session(self.user, topic=None)
        with self.assertRaises(ActiveSessionExists):
            services.start_session(self.user, topic=None)
        other = User.objects.create_user(username='b', password='x')
        services.start_session(other, topic=None)
        self.assertEqual(StudySession.objects.filter(status='RUNNING').count(), 2)

    def test_pause_sets_status_and_paused_at(self):
        services.start_session(self.user, topic=None)
        session = services.pause_session(self.user)
        self.assertEqual(session.status, StudySession.STATUS_PAUSED)
        self.assertIsNotNone(session.paused_at)

    def test_pause_is_idempotent(self):
        services.start_session(self.user, topic=None)
        s1 = services.pause_session(self.user)
        s2 = services.pause_session(self.user)
        self.assertEqual(s1.id, s2.id)
        self.assertEqual(s1.paused_at, s2.paused_at)

    def test_resume_accumulates_paused_time(self):
        services.start_session(self.user, topic=None)
        services.pause_session(self.user)
        StudySession.objects.filter(user=self.user).update(
            paused_at=timezone.now() - timedelta(minutes=10)
        )
        session = services.resume_session(self.user)
        self.assertEqual(session.status, StudySession.STATUS_RUNNING)
        self.assertIsNone(session.paused_at)
        self.assertGreaterEqual(session.total_paused_seconds, 590)
        self.assertLessEqual(session.total_paused_seconds, 620)

    def test_finish_calculates_duration_server_side(self):
        services.start_session(self.user, topic=None)
        StudySession.objects.filter(user=self.user).update(
            start_time=timezone.now() - timedelta(minutes=30)
        )
        session = services.finish_session(self.user)
        self.assertEqual(session.status, StudySession.STATUS_FINISHED)
        self.assertIsNotNone(session.end_time)
        self.assertGreaterEqual(session.duration_minutes, 29)
        self.assertLessEqual(session.duration_minutes, 31)

    def test_finish_discounts_paused_time(self):
        services.start_session(self.user, topic=None)
        StudySession.objects.filter(user=self.user).update(
            start_time=timezone.now() - timedelta(minutes=30)
        )
        services.pause_session(self.user)
        StudySession.objects.filter(user=self.user).update(
            paused_at=timezone.now() - timedelta(minutes=10)
        )
        session = services.finish_session(self.user)
        self.assertGreaterEqual(session.duration_minutes, 19)
        self.assertLessEqual(session.duration_minutes, 21)

    def test_finish_without_active_raises(self):
        with self.assertRaises(NoActiveSession):
            services.finish_session(self.user)

    def test_get_current_returns_none_when_no_active(self):
        self.assertIsNone(services.get_current_session(self.user))

    def test_get_current_returns_active(self):
        s = services.start_session(self.user, topic=None)
        current = services.get_current_session(self.user)
        self.assertEqual(current.id, s.id)

    def test_user_cannot_see_other_user_session(self):
        other = User.objects.create_user(username='b', password='x')
        services.start_session(other, topic=None)
        self.assertIsNone(services.get_current_session(self.user))
