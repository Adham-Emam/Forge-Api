from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase, APIClient
from .models import CustomUser, Notification, Transaction

class CreateUserViewTests(APITestCase):

    def setUp(self):
        self.url = reverse('register')  # Adjust the URL name as per your routing
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'title': 'Software Engineer',
            'education': {},
            'experience': {},
            'skills': ['Java', 'Python'],
            'interests': ['Machine Learning'],
        }

    def test_create_user_success(self):
        response = self.client.post(self.url, self.valid_data, format='json')
        
        # Check for a successful response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the user is created
        user = CustomUser.objects.get(username=self.valid_data['username'])
        self.assertEqual(user.email, self.valid_data['email'])
        self.assertTrue(user.check_password(self.valid_data['password']))

        # Check that the notification was created
        notification = Notification.objects.get(user=user)
        self.assertEqual(notification.type, 'welcome')

        # Verify the response data
        self.assertIn('user', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], "User Created Successfully.  Now perform Login to get your token")

    def test_create_user_invalid_email(self):
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'

        response = self.client.post(self.url, invalid_data, format='json')
        
        # Check for a bad request response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_create_user_missing_username(self):
        invalid_data = self.valid_data.copy()
        invalid_data.pop('username')

        response = self.client.post(self.url, invalid_data, format='json')
        
        # Check for a bad request response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_create_user_duplicate_username(self):
        # Create a user first
        self.client.post(self.url, self.valid_data, format='json')
        
        # Attempt to create another user with the same username
        response = self.client.post(self.url, self.valid_data, format='json')
        
        # Check for a bad request response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_create_user_empty_password(self):
        invalid_data = self.valid_data.copy()
        invalid_data['password'] = ''

        response = self.client.post(self.url, invalid_data, format='json')
        
        # Check for a bad request response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class CurrentUserViewSetTests(APITestCase):
    def setUp(self):
        # Create a user for testing
        self.user = CustomUser.objects.create_user(
            username='testuser',
            first_name='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)  # Authenticate the user for the tests
        self.url = reverse('current-user')  # Assuming you set a URL pattern for this viewset

    def test_retrieve_current_user(self):
        # Test retrieving the current authenticated user
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)  # Adjust based on your serializer fields

    def test_update_current_user(self):
        # Test updating the current authenticated user
        update_data = {
            'first_name': 'updateduser',
            'last_name': 'updateduser'
        }
        response = self.client.patch(self.url, update_data, format='json')  # Use PATCH for partial updates
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Reload the user from the database to check if the changes were saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'updateduser')
        self.assertEqual(self.user.last_name, 'updateduser')


    def test_delete_current_user(self):
        # Test deleting the current authenticated user
        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that the user was actually deleted
        self.assertFalse(CustomUser.objects.filter(id=self.user.id).exists())

    def test_unauthenticated_user_cannot_access(self):
        # Test that an unauthenticated user cannot access the current user endpoint
        self.client.logout()  # Log out the authenticated user
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch(self.url, {'username': 'newname'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationsTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )

        # Create some notifications
        self.notification1 = Notification.objects.create(
            user=self.user,
            message="Notification 1",
            is_read=False
        )
        self.notification2 = Notification.objects.create(
            user=self.user,
            message="Notification 2",
            is_read=True
        )

        self.refresh_token = RefreshToken.for_user(self.user)
        self.token = str(self.refresh_token.access_token)

        # URL for the notifications list
        self.notifications_url = reverse('user-notifications')  # Adjust the name as necessary

    def test_get_notifications_list_authenticated(self):
        response = self.client.get(self.notifications_url, **{'HTTP_AUTHORIZATION': f'Bearer {self.token}'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only unread notifications
        self.assertEqual(response.data[0]['message'], "Notification 1")  # Check content

    def test_get_notifications_list_unauthenticated(self):
        self.client.logout()  # Log out the user
        response = self.client.get(self.notifications_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Expecting forbidden for unauthenticated user


class MarkNotificationAsReadTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.refresh_token = RefreshToken.for_user(self.user)
        self.token = str(self.refresh_token.access_token)

        # Create a notification
        self.notification = Notification.objects.create(
            user=self.user,
            message="Notification to mark as read",
            is_read=False
        )
        self.mark_as_read_url = reverse('notification-detail', args=[self.notification.id])  # Adjust the name and args as necessary

    def test_mark_notification_as_read_authenticated(self):
        response = self.client.patch(self.mark_as_read_url, {'is_read': True}, **{'HTTP_AUTHORIZATION': f'Bearer {self.token}'}, format='json')  # Assuming you can mark it read this way
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()  # Refresh the notification instance
        self.assertTrue(self.notification.is_read)  # Check that it has been marked as read

    def test_mark_notification_as_read_unauthenticated(self):
        self.client.logout()  # Log out the user
        response = self.client.patch(self.mark_as_read_url, {'is_read': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Expecting forbidden for unauthenticated user


class TransactionListTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )

        self.refresh_token = RefreshToken.for_user(self.user)
        self.token = str(self.refresh_token.access_token)


        # Create transactions
        self.received_transaction = Transaction.objects.create(
            user=self.user,
            type="received",
            amount=100
        )
        self.sent_transaction = Transaction.objects.create(
            user=self.user,
            type="payment",
            amount=50
        )

        # URL for the transaction list
        self.received_url = reverse('user-transactions')  # Adjust as necessary
        self.sent_url = reverse('user-transactions')  # Adjust as necessary

    def test_get_received_transactions_authenticated(self):
        response = self.client.get(f'{self.received_url}?type=received', **{'HTTP_AUTHORIZATION': f'Bearer {self.token}'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only received transactions
        self.assertEqual(response.data[0]['amount'], 100)  # Check content

    def test_get_sent_transactions_authenticated(self):
        response = self.client.get(f'{self.sent_url}?type=payment', **{'HTTP_AUTHORIZATION': f'Bearer {self.token}'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only sent transactions
        self.assertEqual(response.data[0]['amount'], 50)  # Check content

    def test_get_transactions_unauthenticated(self):
        self.client.logout()  # Log out the user
        response = self.client.get(self.received_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Expecting forbidden for unauthenticated user