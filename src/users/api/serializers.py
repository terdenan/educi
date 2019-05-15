from rest_framework import serializers
from django.contrib.auth import get_user_model
import django.contrib.auth.password_validation as validators
from django.core import exceptions

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, password):
        errors = {}
        try:
            validators.validate_password(password=password)
        except exceptions.ValidationError as e:
            errors['messages'] = list(e.messages)
        if errors:
            raise serializers.ValidationError(errors)
        return password

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

