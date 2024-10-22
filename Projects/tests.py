from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from .models import Project, Bid
from Users.models import CustomUser


class ProjectListCreateViewTests(APITestCase):
    

    def setUp(self):
        # Create test user
        self.user = CustomUser.objects.create(
            username='testuser',
            email='H5WQp@example.com',
            password='testpassword',
            credits=1000
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


        # Create some sample projects with different attributes
        Project.objects.create(
            title="Python Project", description="A simple Python project", skills_needed=["Python"],
            duration=30, budget=1000, bid_amount=10, type="freelancer", experience_level="beginner",
            owner=self.user
        )

        Project.objects.create(
            title="Django Project", description="A New Django project", skills_needed=["Django"],
            duration=45, budget=2000, bid_amount=20, type="exchange", experience_level="intermediate",
            owner=self.user
        )


    # Test the list view without filters
    def test_list_view_without_filters(self):
        response = self.client.get(reverse('project-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        

    # Test the search Filter
    def test_search_filter(self):
        response = self.client.get(reverse('project-list-create') + '?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Python Project')

        
    # Test Project type filter
    def test_project_type_filter(self):
        response = self.client.get(reverse('project-list-create') + '?project_type=freelancer')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'freelancer')


    # Test Project budget filter
    def test_project_budget_filter(self):
        response = self.client.get(reverse('project-list-create') + '?budget=1000-1500')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['budget'], 1000)


    # Test Project experience level filter
    def test_project_experience_level_filter(self):
        response = self.client.get(reverse('project-list-create') + '?experience_level=beginner')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['experience_level'], 'beginner')

    # Test client history filter
    def test_client_history_filter(self):
        # No client history yet, so no projects should return for the "10+" filter
        response = self.client.get(reverse('project-list-create') + '?client_history=10+')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No projects should match this filter


        # Test project proposal filter
    def test_project_proposals_filter(self):
        response = self.client.get(reverse('project-list-create') + '?proposals=10-20')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


    # Test project creation
    def test_create_project(self):
        project_data = {
            'title': 'New Project',
            'description': 'This is a new test project',
            'skills_needed': ['React', 'Node.js'],
            'duration': 60,
            'budget': 500,
            'bid_amount': 20,
            'type': 'exchange',
            'exchange_for': 'Money',
            'experience_level': 'intermediate'
        }

        
        response = self.client.post(reverse('project-list-create'), project_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 3)  # Ensure a new project has been created
        self.assertEqual(response.data['title'], 'New Project')


    # Test invalid project creation (e.g., negative budget)
    def test_create_project_invalid_data(self):
        invalid_project_data = {
            'title': 'Invalid Project',
            'description': 'This is a test project',
            'skills_needed': ['JavaScript'],
            'duration': 400,  # Invalid duration
            'budget': -500,   # Invalid budget
            'bid_amount': -50,  # Invalid bid amount
            'type': 'Normal',
            'exchange_for': 'Money',
            'experience_level': 'advanced'
        }
        
        response = self.client.post(reverse('project-list-create'), invalid_project_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Project.objects.count(), 2)  # No new project should have been created

    # Test invalid project creation (missing title)
    def test_create_project_missing_title(self):
        invalid_project_data = {
            'description': 'This is a test project',
            'skills_needed': ['JavaScript'],
            'duration': 30,
            'budget': 1000,
            'bid_amount': 10,
            'type': 'freelancer',
            'exchange_for': 'Money',
            'experience_level': 'beginner'
        }

        response = self.client.post(reverse('project-list-create'), invalid_project_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Project.objects.count(), 2)  # No new project should have been created



class ProjectDetailViewTests(APITestCase):
    
    def setUp(self):
        # Create test user
        self.user = CustomUser.objects.create(
            username='testuser',
            email='H5WQp@example.com',
            password='testpassword',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create a sample project
        self.project = Project.objects.create(
            title="Python Project", description="A simple Python project", skills_needed=["Python"],
            duration=30, budget=1000, bid_amount=10, type="freelancer", experience_level="beginner",
            owner=self.user
        )
        self.url = reverse('project-detail', kwargs={'pk': self.project.pk})

    # Test retrieving a project
    def test_retrieve_project(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.project.title)

    # Test updating a project
    def test_update_project(self):
        updated_data = {
            'title': 'Updated Project',
            'description': 'An updated description',
            'skills_needed': ['Python', 'Django'],
            'duration': 60,
            'budget': 600,
            'bid_amount': 20,
            'type': 'exchange',
            'exchange_for': 'Money',
            'experience_level': 'intermediate'
        }
        response = self.client.patch(self.url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'Updated Project')

    # Test deleting a project
    def test_delete_project(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())



class UserProjectsListTests(APITestCase):
    
    def setUp(self):
        # Create test user
        self.user = CustomUser.objects.create(
            username='testuser',
            email='H5WQp@example.com',
            password='testpassword',
            credits=3000
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some sample projects
        self.project1 = Project.objects.create(
            title="Python Project", description="A simple Python project", skills_needed=["Python"],
            duration=30, budget=1000, bid_amount=10, type="freelancer", experience_level="beginner",
            owner=self.user
        )
        self.project2 = Project.objects.create(
            title="Django Project", description="A New Django project", skills_needed=["Django"],
            duration=45, budget=2000, bid_amount=20, type="exchange", experience_level="intermediate",
            owner=self.user
        )
        self.other_user = CustomUser.objects.create(
            username='otheruser',
            email='other@example.com',
            password='testpassword',
        )

    # Test listing projects for the authenticated user
    def test_user_projects_list(self):
        response = self.client.get(reverse('user-projects', kwargs={'user_id': self.user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should return both projects for this user

    # Test listing projects for a different user
    def test_user_projects_list_empty(self):
        response = self.client.get(reverse('user-projects', kwargs={'user_id': self.other_user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Should return no projects for another user



class UserProjectMatchesListTests(APITestCase):
    
    def setUp(self):
        # Create a test user with skills and interests
        self.user = CustomUser.objects.create(
            username='testuser',
            email='testuser@example.com',
            password='testpassword',
            skills=['Python', 'Django'],  # Example skills
            interests=['Machine Learning'],  # Example interests
            credits=3000
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some sample projects
        self.open_project1 = Project.objects.create(
            title="Python Project", 
            description="A simple Python project", 
            skills_needed=["Python"],
            duration=30, 
            budget=1000, 
            bid_amount=10, 
            type="freelancer", 
            experience_level="beginner",
            status='open',  # Mark as open
            owner=self.user
        )
        self.open_project2 = Project.objects.create(
            title="Machine Learning Project", 
            description="A project on machine learning", 
            skills_needed=["Machine Learning"],
            duration=45, 
            budget=2000, 
            bid_amount=20, 
            type="skill exchange", 
            experience_level="intermediate",
            status='open',  # Mark as open
            owner=self.user
        )
        self.closed_project = Project.objects.create(
            title="Old Django Project", 
            description="An outdated project", 
            skills_needed=["Django"],
            duration=60, 
            budget=1500, 
            bid_amount=15, 
            type="freelancer", 
            experience_level="advanced",
            status='closed',  # Mark as closed
            owner=self.user
        )

    # Test retrieving matched projects
    def test_user_project_matches_list(self):
        response = self.client.get(reverse('user-project-matches', kwargs={'user_id': self.user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both open projects should match

    # Test filtering by project type
    def test_project_type_filter(self):
        response = self.client.get(reverse('user-project-matches', kwargs={'user_id': self.user.pk}), 
                                   {'project_type': 'freelancer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only the first project

    # Test filtering by experience level
    def test_experience_level_filter(self):
        response = self.client.get(reverse('user-project-matches', kwargs={'user_id': self.user.pk}), 
                                   {'experience_level': 'intermediate'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only the second project

    # Test filtering by budget
    def test_budget_filter(self):
        response = self.client.get(reverse('user-project-matches', kwargs={'user_id': self.user.pk}), 
                                   {'budget': '500-1500'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only the first project

    # Test filtering by project length
    def test_project_length_filter(self):
        response = self.client.get(reverse('user-project-matches', kwargs={'user_id': self.user.pk}), 
                                   {'project_length': '1-2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should return both projects as their lengths are within range

    # Test filtering by client history
    def test_client_history_filter(self):
        # Assuming the user has not completed any projects yet, expect no results
        response = self.client.get(reverse('user-project-matches', kwargs={'user_id': self.user.pk}), 
                                   {'client_history': '10+'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No projects should match this filter



class UserSavedProjectsListTests(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create(
            username='testuser',
            email='testuser@example.com',
            password='testpassword',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some sample projects
        self.saved_project1 = Project.objects.create(
            title="Python Project", 
            description="A simple Python project", 
            skills_needed=["Python"],
            duration=30, 
            budget=1000, 
            bid_amount=10, 
            type="freelancer", 
            experience_level="beginner",
            owner=self.user
        )
        self.saved_project2 = Project.objects.create(
            title="Machine Learning Project", 
            description="A project on machine learning", 
            skills_needed=["Machine Learning"],
            duration=45, 
            budget=2000, 
            bid_amount=20, 
            type="skill exchange", 
            experience_level="intermediate",
            owner=self.user
        )

        # Simulate saving projects
        self.user.saved_projects.add(self.saved_project1)
        self.user.saved_projects.add(self.saved_project2)

    # Test retrieving saved projects
    def test_user_saved_projects_list(self):
        response = self.client.get(reverse('user-saved-projects', kwargs={'user_id': self.user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both saved projects should match

    # Test filtering by project type
    def test_project_type_filter(self):
        response = self.client.get(reverse('user-saved-projects', kwargs={'user_id': self.user.pk}), 
                                   {'project_type': 'freelancer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only the first project

    # Test filtering by experience level
    def test_experience_level_filter(self):
        response = self.client.get(reverse('user-saved-projects', kwargs={'user_id': self.user.pk}), 
                                   {'experience_level': 'intermediate'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only the second project

    # Test filtering by budget
    def test_budget_filter(self):
        response = self.client.get(reverse('user-saved-projects', kwargs={'user_id': self.user.pk}), 
                                   {'budget': '500-1500'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only the first project

    # Test filtering by project length
    def test_project_length_filter(self):
        response = self.client.get(reverse('user-saved-projects', kwargs={'user_id': self.user.pk}), 
                                   {'project_length': '1-2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should return both saved projects

    # Test filtering by client history
    def test_client_history_filter(self):
        # Assuming the user has not completed any projects yet, expect no results
        response = self.client.get(reverse('user-saved-projects', kwargs={'user_id': self.user.pk}), 
                                   {'client_history': '10+'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No projects should match this filter



class ToggleSavedProjectTests(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create(
            username='testuser',
            email='testuser@example.com',
            password='testpassword',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create a sample project
        self.project = Project.objects.create(
            title="Python Project",
            description="A simple Python project",
            skills_needed=["Python"],
            duration=30,
            budget=1000,
            bid_amount=10,
            type="freelancer",
            experience_level="beginner",
            owner=self.user
        )

    # Test adding a project to saved projects
    def test_toggle_save_project_add(self):
        url = reverse('toggle-saved-project', kwargs={'project_id': self.project.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.project, self.user.saved_projects.all())

    # Test removing a project from saved projects
    def test_toggle_save_project_remove(self):
        # First, save the project
        self.user.saved_projects.add(self.project)
        url = reverse('toggle-saved-project', kwargs={'project_id': self.project.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.project, self.user.saved_projects.all())



class BidListCreateViewTests(APITestCase):
    
    def setUp(self):
        # Create a test user and a project
        self.user = CustomUser.objects.create(
            username='bidderuser',
            email='bidderuser@example.com',
            password='testpassword',
            sparks=50  # Assuming the user has enough sparks
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.owner = CustomUser.objects.create(
            username='projectowner',
            email='projectowner@example.com',
            password='testpassword',
            sparks=0  # Owner has no sparks
        )

        self.project = Project.objects.create(
            title="Java Project",
            description="A simple Java project",
            skills_needed=["Java"],
            duration=30,
            budget=1000,
            bid_amount=10,
            type="freelancer",
            experience_level="beginner",
            owner=self.owner
        )

    # Test creating a valid bid
    def test_create_valid_bid(self):
        url = reverse('project-bids', kwargs={'project_id': self.project.id})
        data = {
            'project': self.project.id,
            'user': self.user.id,
            'proposal': 'I can do this project.',
            'amount': 500,
            'duration': 20,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Bid created successfully')
        self.assertEqual(Bid.objects.count(), 1)

    # Test bidding on one's own project
    def test_bid_on_own_project(self):
        self.client.force_authenticate(user=self.owner)  # Switch to owner
        url = reverse('project-bids', kwargs={'project_id': self.project.id})
        data = {
            'project': self.project.id,
            'proposal': 'I can do this project.',
            'amount': 100,
            'duration': 30
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'You cannot bid on your own project.')

    # Test insufficient sparks for bidding
    def test_bid_insufficient_sparks(self):
        self.user.sparks = 0  # Set sparks to 0
        self.user.save()
        url = reverse('project-bids', kwargs={'project_id': self.project.id})
        data = {
            'project': self.project.id,
            'proposal': 'I can do this project.',
            'amount': 100,
            'duration': 30
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'][0], 'You do not have enough sparks to bid on this project.')

    # Test invalid bid amount
    def test_invalid_bid_amount(self):
        url = reverse('project-bids', kwargs={'project_id': self.project.id})
        data = {
            'project': self.project.id,
            'proposal': 'I can do this project.',
            'amount': 0,  # Invalid amount
            'duration': 30
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'][0], 'Amount must be greater than 0.')

    # Test invalid duration
    def test_invalid_duration(self):
        url = reverse('project-bids', kwargs={'project_id': self.project.id})
        data = {
            'project': self.project.id,
            'proposal': 'I can do this project.',
            'amount': 100,
            'duration': 0,  # Invalid duration
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['duration'][0], 'Ensure this value is greater than or equal to 1.')

    # Test bidding with an amount greater than the budget
    def test_bid_greater_than_budget(self):
        url = reverse('project-bids', kwargs={'project_id': self.project.id})
        data = {
            'project': self.project.id,
            'proposal': 'I can do this project.',
            'amount': 1500,  # Greater than budget
            'duration': 30
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'][0], 'Amount must be less than or equal to the project budget.')


class UsersBidsListTests(APITestCase):

    def setUp(self):


        # Create a user
        self.user = CustomUser.objects.create_user(username='testuser',email='example1@ex.io', password='testpassword')

        self.refresh_token = RefreshToken.for_user(self.user)
        self.token = str(self.refresh_token.access_token)

        # Create another user
        self.other_user = CustomUser.objects.create_user(username='otheruser',email='example2@ex.io', password='otherpassword')

        
        # Create a project owner
        self.owner = CustomUser.objects.create_user(username='testowner',email='example3@ex.io', password='testpassword')

        # Create a project
        self.project = Project.objects.create(
            title="Java Project",
            description="A simple Java project",
            skills_needed=["Java"],
            duration=30,
            budget=1000,
            bid_amount=10,
            type="freelancer",
            experience_level="beginner",
            owner=self.owner
        )

        # Create bids for the users
        self.user_bid = Bid.objects.create(user=self.user, project=self.project, amount=100)
        self.other_user_bid = Bid.objects.create(user=self.other_user, project=self.project, amount=200)

        # Set up the API client
        self.client = APIClient()

    def test_authenticated_user_gets_own_bids(self):
        # Get the user's bids
        url = reverse('user-bids-list') 
        response = self.client.get(url, format='json')

        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the user receives only their own bids
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user.id)

    def test_unauthenticated_user_cannot_access_bids(self):
        # Attempt to get bids without authentication
        url = reverse('user-bids-list') 
        response = self.client.get(url ,  **{'HTTP_AUTHORIZATION': f'Bearer {self.token}'}, format='json')

        # Ensure the response is forbidden (or allowed for read-only access)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_user_cannot_see_another_user_bids(self):

        # Get the other user's bids
        url = reverse('user-bids-list') 
        response = self.client.get(url ,  **{'HTTP_AUTHORIZATION': f'Bearer {self.token}'}, format='json')

        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the other user only sees their own bids
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.other_user.id)