from rest_framework import serializers
from .models import Project, Bid
from django.core.exceptions import ValidationError, PermissionDenied


class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    owner_first_name = serializers.ReadOnlyField(source='owner.first_name')
    owner_last_name = serializers.ReadOnlyField(source='owner.last_name')
    owner_title = serializers.ReadOnlyField(source='owner.user_title')
    owner_location = serializers.ReadOnlyField(source='owner.country')
    bids = serializers.SerializerMethodField() 


    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_bids(self, obj):
        # Assuming a ForeignKey relationship: Bid.project
        return Bid.objects.filter(project=obj).count()

class BidSerializer(serializers.ModelSerializer):
    bidder_first_name = serializers.ReadOnlyField(source='user.first_name')
    bidder_last_name = serializers.ReadOnlyField(source='user.last_name')
    project_title = serializers.ReadOnlyField(source='project.title')
    project_description = serializers.ReadOnlyField(source='project.description')

    class Meta:
        model = Bid
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user', 'project']
    
    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except ValidationError as e:
            reformatted_errors = {'error': e.detail}
            raise reformatted_errors

    def validate(self, attrs):
        user = self.context['request'].user
        project_id = self.context['project_id']
        project = Project.objects.get(id=project_id)

        # Custom validation logic
        if user == project.owner:
            raise PermissionDenied({'error': 'You cannot bid on your own project.'})
        
        if user.sparks < project.bid_amount:
            raise ValidationError({'error': 'You do not have enough sparks to bid on this project.'})
        
        if attrs.get('duration', 0) < 1 or attrs.get('duration', 0) > 365:
            raise ValidationError({'error': 'Duration must be between 1 and 365 days.'})
        
        if attrs.get('amount', 0) <= 0:
            raise ValidationError({'error': 'Amount must be greater than 0.'})
        
        if attrs.get('amount', 0) > project.budget:
            raise ValidationError({'error': 'Amount must be less than or equal to the project budget.'})

        return attrs