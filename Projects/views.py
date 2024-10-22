from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from .models import Project, Bid
from Users.models import CustomUser, Notification, Transaction
from .serializers import ProjectSerializer, BidSerializer
from rest_framework.permissions import  IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.db import IntegrityError


class ProjectPagination(PageNumberPagination):
    page_size = 10  # Number of projects per page
    page_size_query_param = 'page_size'  # Allow client to control page size with a query param
    max_page_size = 100  # Max page size allowed



class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = ProjectPagination


    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Access the query parameters
        query = self.request.query_params.get('search')
        project_type = self.request.query_params.get('project_type')
        experience_level = self.request.query_params.get('experience_level')  # e.g., "beginner,intermediate"
        budget = self.request.query_params.get('budget')  # e.g., "23-42"
        country = self.request.query_params.get('country')
        proposals = self.request.query_params.get('proposals')
        project_length = self.request.query_params.get('project_length')
        client_history = self.request.query_params.get('client_history')


        # Apply the search query first if it exists
        if not query:
            queryset = queryset
        else:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(skills_needed__icontains=query)
            )

        # Handle the project type filter (Normal, Skill Exchange)
        if project_type:
            project_type_list = project_type.split(',')
            queryset = queryset.filter(type__in=project_type_list)


        # Handle the budget query
        if budget:
            try:
                min_budget, max_budget = map(int, budget.split('-'))
                if min_budget is not None:
                    queryset = queryset.filter(budget__gte=min_budget)
                if max_budget is not None:
                    queryset = queryset.filter(budget__lte=max_budget)
            except ValueError:
                return queryset.none()  # Return an empty queryset on invalid format


        # Filter by experience level
        if experience_level:
            experience_level_list = experience_level.split(',')
            queryset = queryset.filter(experience_level__in=experience_level_list)

        # Filter by country
        if country:
            queryset = queryset.filter(owner__country=country)

        # Filter by proposals
        if proposals:
            proposal_ranges = proposals.split(',')
            filters = Q()  

            # Annotate each project with the number of bids
            queryset = queryset.annotate(bid_count=Count('bids'))

            for proposal_range in proposal_ranges:
                try:
                    # Only process valid proposal ranges, skipping invalid ones
                    if '-' in proposal_range and proposal_range.replace('-', '').isdigit():
                        min_proposal, max_proposal = map(int, proposal_range.split('-'))
                        filters |= Q(bids__gte=min_proposal, bids__lte=max_proposal)
                except ValueError:
                    continue  # Skip any invalid ranges

            queryset = queryset.filter(filters)

        # Filter by project length (in months, converting to days)
        if project_length:
            project_length_ranges = project_length.split(',')
            filters = Q()  # Empty Q object to chain multiple ranges
        
            for project_length_range in project_length_ranges:
                try:
                    min_project_length, max_project_length = map(int, project_length_range.split('-'))
        
                    # Convert months to days (assuming 30.44 days per month)
                    min_days = round(min_project_length * 30.44)
                    max_days = round(max_project_length * 30.44)

                    # Add each range as a filter
                    filters |= Q(duration__gte=min_days, duration__lte=max_days)
                
                except ValueError:
                    continue  # Skip invalid ranges in case of errors
            
            queryset = queryset.filter(filters)

        
        # Filter by client history (count completed projects per client)
        if client_history:
            client_history_ranges = client_history.split(',')
            filters = Q()

            # Annotate the queryset with the count of completed projects for each client
            queryset = queryset.annotate(
                completed_projects=Count('owner__projects', filter=Q(owner__projects__status='completed'))
            )

            # Apply the filters based on the client history ranges
            for history_range in client_history_ranges:
                if history_range == "10+":  # Special case for "10+"
                    filters |= Q(completed_projects__gte=10)
                elif '-' in history_range:  # Handle ranges like "1-9"
                    try:
                        min_projects, max_projects = map(int, history_range.split('-'))
                        filters |= Q(completed_projects__gte=min_projects, completed_projects__lte=max_projects)
                    except ValueError:
                        continue  # Skip invalid ranges
                else:  # Handle single values like "0"
                    try:
                        min_projects = int(history_range)
                        filters |= Q(completed_projects__exact=min_projects)
                    except ValueError:
                        continue  # Skip invalid values

            queryset = queryset.filter(filters)

        return queryset.distinct()

    def post(self, request):
        user = request.user
        title = request.data.get('title')
        description = request.data.get('description')
        skills_needed = request.data.get('skills_needed')
        duration = request.data.get('duration')
        budget = request.data.get('budget')
        bid_amount = request.data.get('bid_amount')
        type = request.data.get('type')
        exchange_for = request.data.get('exchange_for')
        experience_level = request.data.get('experience_level')

        if not title or not description or not skills_needed or not duration or not budget or not bid_amount or not type:
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if duration < 1 or duration > 365:
            return Response({'error': 'Duration must be between 1 and 365 days.'}, status=status.HTTP_400_BAD_REQUEST)
        elif budget <= 0:
            return Response({'error': 'Budget must be greater than 0.'}, status=status.HTTP_400_BAD_REQUEST)
        elif bid_amount <= 0:
            return Response({'error': 'Bid amount must be greater than 0.'}, status=status.HTTP_400_BAD_REQUEST)
        elif budget > user.credits:
            return Response({'error': 'Insufficient credits, Please purchase more Embers.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.create(
                title=title,
                description=description,
                skills_needed=skills_needed,
                duration=duration,
                budget=budget,
                bid_amount=bid_amount,
                type=type,
                exchange_for=exchange_for,
                experience_level=experience_level,
                owner=user
            )
            project.save()
            
            # Send notification to the project owner
            notification = Notification.objects.create(
                user=user,
                type='project',
                url= f'/dashboard/projects/{project.id}?title={project.title}&description={project.description}',
                message='Congratulations! Your project has been successfully created on our platform. Now, talented freelancers can discover it and submit their proposals. Keep an eye on your inbox for updates!'
            )
            notification.save()



            return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error': 'Project already exists.'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class UserProjectsList(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        user = get_object_or_404(CustomUser, id=user_id)
        status = self.request.query_params.get('status')

        if status == 'open':
            return Project.objects.filter(owner=user, status='open', assigned_to=None)
        elif status == 'in_progress':
            return Project.objects.filter(status='in_progress', assigned_to=user)
        elif status == 'my_in_progress':
            return Project.objects.filter(owner=user, status='in_progress')
        elif status == 'closed':
            return Project.objects.filter(owner=user, status='closed')
        return Project.objects.filter(owner=user)

class UserProjectMatchesList(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ProjectSerializer
    pagination_class = ProjectPagination

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Start with open projects
        queryset = Project.objects.filter(status='open')

        # Filter projects that match user's skills or interests
        project_ids = []
        for project in queryset:
            if any(skill in user.skills for skill in project.skills_needed) or any(interest in user.interests for interest in project.skills_needed):
                project_ids.append(project.id)

        queryset = queryset.filter(id__in=project_ids)

        # Access the query parameters for additional filters
        project_type = self.request.query_params.get('project_type')
        experience_level = self.request.query_params.get('experience_level')
        budget = self.request.query_params.get('budget')
        country = self.request.query_params.get('country')
        proposals = self.request.query_params.get('proposals')
        project_length = self.request.query_params.get('project_length')
        client_history = self.request.query_params.get('client_history')

        # Handle the project type filter (Normal, Skill Exchange)
        if project_type:
            project_type_list = project_type.split(',')
            queryset = queryset.filter(type__in=project_type_list)

        # Handle the budget query
        if budget:
            try:
                min_budget, max_budget = map(int, budget.split('-'))
                if min_budget is not None:
                    queryset = queryset.filter(budget__gte=min_budget)
                if max_budget is not None:
                    queryset = queryset.filter(budget__lte=max_budget)
            except ValueError:
                return queryset.none()  # Return an empty queryset on invalid format

        # Filter by experience level
        if experience_level:
            experience_level_list = experience_level.split(',')
            queryset = queryset.filter(experience_level__in=experience_level_list)

        # Filter by country
        if country:
            queryset = queryset.filter(owner__country=country)

        # Filter by proposals
        if proposals:
            proposal_ranges = proposals.split(',')
            filters = Q()  
            # Annotate each project with the number of bids
            queryset = queryset.annotate(bid_count=Count('bids'))

            for proposal_range in proposal_ranges:
                min_proposal, max_proposal = map(int, proposal_range.split('-'))
                filters |= Q(bids__gte=min_proposal, bids__lte=max_proposal)

            queryset = queryset.filter(filters)

        # Filter by project length (in months, converting to days)
        if project_length:
            project_length_ranges = project_length.split(',')
            filters = Q()  # Empty Q object to chain multiple ranges
        
            for project_length_range in project_length_ranges:
                try:
                    min_project_length, max_project_length = map(int, project_length_range.split('-'))
                    # Convert months to days (assuming 30.44 days per month)
                    min_days = round(min_project_length * 30.44)
                    max_days = round(max_project_length * 30.44)

                    # Add each range as a filter
                    filters |= Q(duration__gte=min_days, duration__lte=max_days)
                
                except ValueError:
                    continue  # Skip invalid ranges in case of errors
            
            queryset = queryset.filter(filters)

        # Filter by client history (count completed projects per client)
        if client_history:
            client_history_ranges = client_history.split(',')
            filters = Q()

            # Annotate the queryset with the count of completed projects for each client
            queryset = queryset.annotate(
                completed_projects=Count('owner__projects', filter=Q(owner__projects__status='completed'))
            )

            # Apply the filters based on the client history ranges
            for history_range in client_history_ranges:
                if history_range == "10+":  # Special case for "10+"
                    filters |= Q(completed_projects__gte=10)
                else:
                    min_projects, max_projects = map(int, history_range.split('-'))
                    filters |= Q(completed_projects__gte=min_projects, completed_projects__lte=max_projects)

            queryset = queryset.filter(filters)

        return queryset.distinct()

class UserSavedProjectsList(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ProjectSerializer
    pagination_class = ProjectPagination

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Start with the user's saved projects
        queryset = user.saved_projects.all()

        # Access the query parameters for filtering
        project_type = self.request.query_params.get('project_type')
        experience_level = self.request.query_params.get('experience_level')
        budget = self.request.query_params.get('budget')
        country = self.request.query_params.get('country')
        proposals = self.request.query_params.get('proposals')
        project_length = self.request.query_params.get('project_length')
        client_history = self.request.query_params.get('client_history')

        # Handle project type filter
        if project_type:
            project_type_list = project_type.split(',')
            queryset = queryset.filter(type__in=project_type_list)

        # Handle the budget filter
        if budget:
            try:
                min_budget, max_budget = map(int, budget.split('-'))
                if min_budget is not None:
                    queryset = queryset.filter(budget__gte=min_budget)
                if max_budget is not None:
                    queryset = queryset.filter(budget__lte=max_budget)
            except ValueError:
                return queryset.none()  # Return empty queryset on invalid format

        # Filter by experience level
        if experience_level:
            experience_level_list = experience_level.split(',')
            queryset = queryset.filter(experience_level__in=experience_level_list)

        # Filter by country
        if country:
            queryset = queryset.filter(owner__country=country)

        # Filter by proposals
        if proposals:
            proposal_ranges = proposals.split(',')
            filters = Q()  

            # Annotate each project with the number of bids
            queryset = queryset.annotate(bid_count=Count('bids'))

            for proposal_range in proposal_ranges:
                min_proposal, max_proposal = map(int, proposal_range.split('-'))
                filters |= Q(bids__gte=min_proposal, bids__lte=max_proposal)

            queryset = queryset.filter(filters)

        # Filter by project length (in months, converting to days)
        if project_length:
            project_length_ranges = project_length.split(',')
            filters = Q()  # Empty Q object to chain multiple ranges

            for project_length_range in project_length_ranges:
                try:
                    min_project_length, max_project_length = map(int, project_length_range.split('-'))
                    min_days = round(min_project_length * 30.44)  # Convert months to days
                    max_days = round(max_project_length * 30.44)

                    filters |= Q(duration__gte=min_days, duration__lte=max_days)

                except ValueError:
                    continue  # Skip invalid ranges

            queryset = queryset.filter(filters)

        # Filter by client history
        if client_history:
            client_history_ranges = client_history.split(',')
            filters = Q()

            # Annotate the queryset with the count of completed projects for each client
            queryset = queryset.annotate(
                completed_projects=Count('owner__projects', filter=Q(owner__projects__status='completed'))
            )

            for history_range in client_history_ranges:
                if history_range == "10+":  # Special case for "10+"
                    filters |= Q(completed_projects__gte=10)
                else:
                    min_projects, max_projects = map(int, history_range.split('-'))
                    filters |= Q(completed_projects__gte=min_projects, completed_projects__lte=max_projects)

            queryset = queryset.filter(filters)

        return queryset.distinct()

class ToggleSavedProject(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ProjectSerializer

    def post(self, request, *args, **kwargs):
        user_id = self.request.user.id
        project_id = self.kwargs.get('project_id')

        # Get the user and project objects
        user = get_object_or_404(CustomUser, id=user_id)
        project = get_object_or_404(Project, id=project_id)

        # Toggle saving/removing the project
        if project in user.saved_projects.all():
            user.saved_projects.remove(project)
            message = 'Project removed from saved projects'
        else:
            user.saved_projects.add(project)
            message = 'Project added to saved projects'

        return Response({'message': message}, status=status.HTTP_200_OK)


class BidListCreateView(generics.ListCreateAPIView):
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Bid.objects.filter(project=project_id)


    def post(self, request, **kwargs):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        user = self.request.user
        proposal = self.request.data.get('proposal')
        amount = self.request.data.get('amount')
        duration = self.request.data.get('duration')
        

        # Include the project in the request data for validation purposes
        data = request.data.copy()  
        data['project'] = project_id  

        try:
            # Validate the request data
            serializer = BidSerializer(data=data, context={'request': request, 'project_id': project_id })

            # Validate the data
            serializer.is_valid(raise_exception=True)
            # If validation passes, create the bid
            serializer.save(user=user, project=project, proposal=proposal, amount=amount, duration=duration)


            # Reduce sparks
            user.sparks -= project.bid_amount
            user.save()

            # Create the transaction
            Transaction.objects.create(
                user=user,
                currency='spark',
                type='payment',
                description='Bid on project',
                amount=project.bid_amount,
            )

            # Send Notification to the project owner
            Notification.objects.create(
                user=project.owner,
                type="bid",
                url=f"/dashboard/projects/{project.id}?title={project.title}&description={project.description}",
                message=f"{user.first_name} {user.last_name} has submitted a bid on your project."
            )

            return Response({'message': 'Bid created successfully'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            # Handle the case where a duplicate bid is attempted
            raise ValidationError({'error': 'You cannot apply again for this project.'})


class UsersBidsList(generics.ListAPIView):
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        status = self.request.query_params.get('status')
        owner = self.request.query_params.get('owner', 'false')

        if status == 'open':
            return Bid.objects.filter(user=user, project__status='open')
        elif status == 'in_progress':
            return Bid.objects.filter(project__status='in_progress', project__assigned_to=user)
        elif owner == 'true':
            return Bid.objects.filter(project__owner=user, project__status='open', project__assigned_to=None)

        return Bid.objects.filter(user=user, project__status__in=['open', 'in_progress', 'closed'])
