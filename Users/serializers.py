from rest_framework import serializers
from .models import CustomUser, Notification, Transaction, Subscriber, Message
from datetime import datetime

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'password',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        """
        Validate that the given username is not already in use.

        Args:
            value (str): The username to validate.

        Returns:
            str: The validated username.

        Raises:
            serializers.ValidationError: If the username is already in use.
        """
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already in use.")
        return value

    def validate_email(self, value):
        """
        Validate that the given email is not already in use.

        Args:
            value (str): The email to validate.

        Returns:
            str: The validated email.

        Raises:
            serializers.ValidationError: If the email is already in use.
        """

        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def create(self, validated_data):
        """
        Create a new user with the given validated data.

        Args:
            validated_data (dict): The validated data to create a new user with.

        Returns:
            CustomUser: The newly created user.
        """
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields ='__all__'
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ['id', 'created_at', 'updated_at', 'username','credits','sparks', 'email']


    def validate_gender(self, value):
        if value not in ['Male', 'Female', 'Prefer not to say', None]:  # Add more gender options if needed
            raise serializers.ValidationError("Gender must be either 'Male', 'Female', or ''.")
        return value

    def validate_skills(self, value):
        # Check if skills is a list and not empty
        if not isinstance(value, list) or not all(isinstance(skill, str) for skill in value):
            raise serializers.ValidationError("Skills must be a list of strings.")
        if not value:
            raise serializers.ValidationError("Skills may not be empty.")
        return value

    def validate_interests(self, value):
        # Check if interests is a list and not empty
        if not isinstance(value, list) or not all(isinstance(interest, str) for interest in value):
            raise serializers.ValidationError("Interests must be a list of strings.")
        if not value:
            raise serializers.ValidationError("Interests may not be empty.")
        return value

    def validate_birth_date(self, value):
        # Ensure the birth date is not in the future
        if value and value > datetime.date.today():
            raise serializers.ValidationError("Birth date cannot be in the future.")
        return value

    def validate(self, attrs):
        # Add any additional cross-field validation if necessary
        return super().validate(attrs)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class SubscriberSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Subscriber
        fields = '__all__'
        read_only_fields = ['id']


    # Field-level validation
    def validate_email(self, value):
        if Subscriber.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already subscribed.")
        return value

    # Object-level validation
    def validate(self, data):
        # Add any custom object-level validation here if needed
        return data



class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['id', 'created_at']