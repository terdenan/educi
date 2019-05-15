from rest_framework import serializers

from build_rules.models import Rule


class RuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rule
        fields = ('id', 'title', 'description', 'order', 'command', 'timeout', 'continue_on_fail')

    def create(self, validated_data):
        assignment = self.context.get('assignment', None)
        rule = Rule.objects.create(assignment=assignment, **validated_data)
        return rule
