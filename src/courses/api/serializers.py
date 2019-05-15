from rest_framework import serializers

from users.models import User
from courses.models import Course, Membership, Assignment, Environment, CourseCreationRequest


class CourseMembersSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Membership
        fields = ('user_id', 'email', 'role')

    def create(self, validated_data):
        course = self.context.get('course', None)

        email = validated_data['user']['email']
        user = User.objects.get(email=email)
        role = validated_data['role']

        return course.add_member(user, role)


class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ('id', 'title', 'description')


class CourseCreationRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseCreationRequest
        fields = ('id', 'title', 'description', 'status')
        read_only_fields = ('id', 'status')

    def create(self, validated_data):
        user = self.context.get('user', None)
        return CourseCreationRequest.objects.create(user=user, **validated_data)


class EnvironmentSerializer(serializers.ModelSerializer):
    course = serializers.ReadOnlyField(source='course.id')

    class Meta:
        model = Environment
        fields = ('id', 'title', 'course', 'tag', 'status', 'dockerfile_content')
        read_only_fields = ('id', 'status')

    def create(self, validated_data):
        course = self.context.get('course', None)
        return Environment.objects.create(course=course, **validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.tag = validated_data.get('tag', instance.tag)
        instance.dockerfile_content = validated_data.get('dockerfile_content', instance.dockerfile_content)
        instance.save(update_fields=validated_data.keys())
        return instance


class AssignmentSerializer(serializers.ModelSerializer):
    course_id = serializers.ReadOnlyField(source='course.id')

    class Meta:
        model = Assignment
        fields = ('id', 'environment', 'course_id', 'title', 'description')

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

    def create(self, validated_data):
        course = self.context.get('course', None)
        return course.add_assignment(**validated_data)
