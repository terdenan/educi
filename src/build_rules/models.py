from django.db import models, transaction
from django.db.models import F, Max
from django.core.validators import MinValueValidator

from courses.models import Assignment


class RuleManager(models.Manager):
    # @see: https://www.revsys.com/tidbits/keeping-django-model-objects-ordered/

    def move(self, obj, new_order):
        """ Move an object to a new order position """
        qs = self.get_queryset()

        with transaction.atomic():
            if obj.order > int(new_order):
                qs.filter(
                    assignment=obj.assignment,
                    order__lt=obj.order,
                    order__gte=new_order
                ).exclude(
                    pk=obj.pk
                ).update(
                    order=F('order') + 1
                )
            else:
                qs.filter(
                    assignment=obj.assignment,
                    order__lte=new_order,
                    order__gt=obj.order
                ).exclude(
                    pk=obj.pk
                ).update(
                    order=F('order') - 1
                )

            obj.order = new_order
            obj.save()

    def create(self, **kwargs):
        instance = self.model(**kwargs)

        with transaction.atomic():
            results = self.filter(
                assignment=instance.assignment
            ).aggregate(
                Max('order')
            )

            current_order = results['order__max']
            if current_order is None:
                current_order = 0

            value = current_order + 1
            instance.order = value
            instance.save()
            return instance


class Rule(models.Model):
    title = models.CharField(max_length=60)
    description = models.CharField(max_length=255, default="")
    order = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    command = models.CharField(max_length=255)
    timeout = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    continue_on_fail = models.BooleanField(default=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='rules')

    objects = RuleManager()

    class Meta:
        index_together = ('assignment', 'order')

    def __str__(self):
        return self.title
