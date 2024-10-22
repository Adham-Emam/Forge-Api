from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from .models import CustomUser, Notification, Transaction, Subscriber, Message
from Projects.models import Project
from .serializers import CreateUserSerializer, CustomUserSerializer, NotificationSerializer, TransactionSerializer, SubscriberSerializer, MessageSerializer
from django.db.models import Q


class CreateUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]


    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        notification = Notification.objects.create(
            user=user,
            type="welcome",
            url=f"/dashboard/profile/{user.id}?username={user.first_name}+{user.last_name}&title={user.user_title}",
            message="Welcome to Forge! Get started by creating a project.",
        )
        notification.save()

        email = self.request.data['email']
        subscriber = Subscriber.objects.create(email=email)
        subscriber.save()

        return Response({
            "user": CustomUserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User Created Successfully.  Now perform Login to get your token",
        }, status=status.HTTP_201_CREATED)


class UserRetrieveUsernameWithEmailView(generics.GenericAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        email = self.request.data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
            return Response({'username': user.username})  # Return a dict
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found'}, status=404)  # Return a 404 if not found

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CurrentUserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request):
        user = request.user
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)

    def update(self, request):
        user = request.user
        serializer = CustomUserSerializer(
            user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotificationsList(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user.id
        return Notification.objects.filter(user=user, is_read=False)
    
class MarkNotificationAsRead(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.id
        return Notification.objects.filter(user=user, is_read=False)
    

class TransactionList(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.id
        transaction_type = self.request.query_params.get('type', None)

        if transaction_type == "received":
            return Transaction.objects.filter(user=user, type="received")
        elif transaction_type == "payment":
            return Transaction.objects.filter(user=user , type="payment")
        else :
            return Transaction.objects.filter(user=user)


class SubscribersListView(generics.ListCreateAPIView):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    authentication_classes = []
    permission_classes = [AllowAny]


class UnSubscribeView(generics.DestroyAPIView):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        # Get the email from the request data
        email = self.request.data.get('email')

        # Validate that email is provided
        if not email:
            raise ValidationError({'message': "Email is required for unsubscribing."})

        try:
            # Try to get the subscriber by email
            subscriber = Subscriber.objects.get(email=email)
            return subscriber
        except Subscriber.DoesNotExist:
            raise NotFound({'message': "Subscriber with this email not found."})

    def delete(self, request, *args, **kwargs):
        # Call get_object to retrieve and validate the subscriber
        subscriber = self.get_object()
        subscriber.delete()  # Delete the subscriber from the database
        return Response({"message": "Successfully unsubscribed"}, status=status.HTTP_204_NO_CONTENT)



class UserContactsView(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        assigned_to = Project.objects.filter(owner=user).values_list('assigned_to', flat=True).distinct()
        assigned_to_me = Project.objects.filter(assigned_to=user).values_list('owner', flat=True).distinct()

        # Base queryset for contacts
        queryset = CustomUser.objects.filter(Q(id__in=assigned_to) | Q(id__in=assigned_to_me))

        # Check if there is a search parameter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        
        return queryset

class UserMessagesView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        other_user = self.request.query_params.get('other_user')

        return Message.objects.filter(sender=user, receiver=other_user) | Message.objects.filter(sender=other_user, receiver=user)