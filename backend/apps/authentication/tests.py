"""Authentication API tests."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import User
from employees.models import Department, Employee


class AuthAPITestCase(APITestCase):
    def setUp(self):
        self.it_user = User.objects.create_user(
            username="it.auth",
            email="it.auth@example.com",
            password="TestPass123!",
            role=User.Role.IT_TEAM,
        )
        self.orphan = User.objects.create_user(
            username="orphan",
            email="orphan@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYEE,
        )
        self.linked = User.objects.create_user(
            username="linked",
            email="linked@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYEE,
        )
        dept = Department.objects.create(name="Engineering", code="ENG")
        Employee.objects.create(
            user=self.linked,
            department=dept,
            employee_code="E001",
        )

    def test_me_requires_auth(self):
        response = self.client.get(reverse("authentication:me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile(self):
        self.client.force_authenticate(user=self.linked)
        response = self.client.get(reverse("authentication:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.linked.email)
        self.assertEqual(response.data["employee_profile"]["employee_code"], "E001")

    def test_users_list_without_employee(self):
        self.client.force_authenticate(user=self.it_user)
        response = self.client.get(
            reverse("authentication:users_list"),
            {"without_employee": "true"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {u["id"] for u in response.data["results"]}
        self.assertIn(self.orphan.id, ids)
        self.assertIn(self.it_user.id, ids)
        self.assertNotIn(self.linked.id, ids)

    def test_users_list_denied_for_employee(self):
        self.client.force_authenticate(user=self.orphan)
        response = self.client.get(reverse("authentication:users_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
