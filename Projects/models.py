from django.db import models
from Users.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator



class Project(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    )
    TYPE_CHOICES = (
        ('exchange', 'Exchange'),
        ('freelancer', 'Freelancer'),
    )

    EXPERIENCE_LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    skills_needed = models.JSONField(default=list, blank=True)
    budget = models.IntegerField()
    duration = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(365)])

    bid_amount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(40)])
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open')
    owner = models.ForeignKey(
        CustomUser, related_name='projects', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(
        CustomUser, related_name='assigned_projects', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='freelancer')
    exchange_for = models.TextField(null=True, blank=True)

    experience_level= models.CharField(max_length=20, null=True, choices=EXPERIENCE_LEVEL_CHOICES)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('title', 'owner')
        
    def __str__(self):
        return self.title

class Bid(models.Model):
    project = models.ForeignKey(Project, related_name='bids', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name='bids', on_delete=models.CASCADE)
    proposal = models.TextField(null=True)
    amount = models.IntegerField()
    duration = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(365)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')  # Prevent duplicate bids from the same user


    def __str__(self):
        return self.user.username