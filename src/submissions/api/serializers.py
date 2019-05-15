from rest_framework import serializers

from submissions.models import Submission


class SubmissionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.StringRelatedField(source='assignment.title')
    user_email = serializers.StringRelatedField(source='user.email')
    reviewer_email = serializers.StringRelatedField(source='reviewer.email')
    type = serializers.CharField(write_only=True)

    class Meta:
        model = Submission
        fields = ('id', 'assignment', 'assignment_title', 'user', 'user_email', 'repo_url', 'branch', 'type',
                  'source', 'datetime', 'reviewer', 'reviewer_email', 'status', 'stdout', 'stderr')
        read_only_fields = ('id', 'user', 'user_email', 'reviewer', 'reviewer_email',
                            'assignment_title', 'stdout', 'stderr')
        extra_kwargs = {'source': {'write_only': True}}

    def validate(self, data):
        download_type = data.get('type', None)

        if download_type is None:
            raise serializers.ValidationError("Download type must be provided")

        allowed = True

        if download_type == Submission.STRATEGY_REPOSITORY:
            allowed = 'repo_url' in data and data['repo_url'] != "" and \
                      'branch' in data and data['branch'] != ""
        elif download_type == Submission.STRATEGY_SOURCES:
            allowed = 'source' in data
        else:
            allowed = False

        if not allowed:
            raise serializers.ValidationError("Invalid download type or invalid respective fields")

        return data

    def create(self, validated_data):
        download_type = validated_data['type']

        assignment = validated_data['assignment']
        user = validated_data['user']

        repo_url = validated_data.get('repo_url', "")
        branch = validated_data.get('branch', "")
        source = validated_data.get('source', None)

        submission = Submission(assignment=assignment, user=user,
                                repo_url=repo_url, branch=branch, source=source)
        submission.save(download_type=download_type)

        return submission


class SubmissionUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = ('reviewer',)
