from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@hotmail.com",
            password = "1234test"
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="test@hotmail.com",
            password = "1234test",
            name= "Test user full name"
        )

    def test_users_listed(self):
        """Test users are listed on user page"""
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        # assertContains method is django specific assert which looks first
        # to the http status (if 200) and then checks the response content and 
        # compares it with the provided data
        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """Test that the user edit page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        # /admin/core/user/1
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)


    def test_user_create_page(self):
        """Tests that the create user page works"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        