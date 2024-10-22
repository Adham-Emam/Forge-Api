from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class CustomUser(AbstractUser):
    profile_image = models.ImageField(
        upload_to='profile_images/', blank=True, null=True)
    user_title = models.CharField(max_length=255, null=True, blank=True)
    credits = models.IntegerField(default=0)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(max_length=5000, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    # Education field: list of dictionaries
    education = models.JSONField(default=list, blank=True)

    # Experience field: list of dictionaries
    experience = models.JSONField(default=list, blank=True)

    # Skills and Interests: lists of strings
    skills = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)

    # Social profiles
    website_url = models.URLField(null=True, blank=True)
    linkedin_profile = models.URLField(null=True, blank=True)
    github_profile = models.URLField(null=True, blank=True)
    twitter_profile = models.URLField(null=True, blank=True)
    reddit_profile = models.URLField(null=True, blank=True)
    instagram_profile = models.URLField(null=True, blank=True)
    linktree_profile = models.URLField(null=True, blank=True)


    # Saved projects IDs
    saved_projects = models.ManyToManyField('Projects.Project', related_name='saved_by', blank=True)
    
    sparks = models.IntegerField(default=100)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",  # Custom related name
        blank=True
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set_permissions",  # Custom related name
        blank=True
    )

    def __str__(self):
        return self.username


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('welcome', 'Welcome'),
        ('message', 'Message'),
        ('project', 'Project'),
        ('bid', 'Bid'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    type = models.CharField(max_length=255, choices=NOTIFICATION_TYPE_CHOICES)
    url = models.URLField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.user.username
    

class Transaction(models.Model):
    CURRENCY_CHOICES = (
        ('ember', 'Ember'),
        ('spark', 'Spark'),
    )
    TYPE_CHOICES = (
        ('received', 'Received'),
        ('payment', 'Payment'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    currency = models.CharField(max_length=255, choices=CURRENCY_CHOICES)
    amount = models.IntegerField()
    type = models.CharField(max_length=255, choices=TYPE_CHOICES, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    

class Subscriber(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email


class Message(models.Model):
    sender = models.ForeignKey(CustomUser, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.user.username