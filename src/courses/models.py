from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from courses.tasks import create_docker_image, update_docker_image, delete_docker_image

User = get_user_model()


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    members = models.ManyToManyField(User, through='Membership')

    @property
    def attachments_path(self):
        return f"courses/course_{self.id}/attachments"

    def add_member(self, user, role):
        return Membership.objects.create(user=user, course=self, role=role)

    def remove_member(self, user_id):
        Membership.objects.get(user__id=user_id).delete()

    def has_member(self, user_id):
        return Membership.objects.filter(user__id=user_id).exists()

    def add_assignment(self, title, description, environment):
        return Assignment.objects.create(course=self, title=title, description=description, environment=environment)

    def remove_assignment(self, assignment_id):
        Assignment.objects.get(pk=assignment_id).delete()

    def get_role(self, user):
        try:
            entry = Membership.objects.filter(course=self, user=user).get()
        except ObjectDoesNotExist:
            return None

        return entry.role

    def __str__(self):
        return self.title


class CourseCreationRequest(models.Model):
    CONSIDERING = 0
    APPROVED = 1
    REFUSED = 2

    STATUS_CHOICES = (
        (CONSIDERING, 'Considering'),
        (APPROVED, 'Approved'),
        (REFUSED, 'Refused'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=CONSIDERING)

    def __str__(self):
        return f'{self.user.email} - {self.title}'


class Membership(models.Model):
    TEACHER = 0
    TA = 1
    STUDENT = 2

    ROLES_CHOICES = (
        (TEACHER, 'Teacher'),
        (TA, 'Teacher Assistant'),
        (STUDENT, 'Student'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    role = models.PositiveSmallIntegerField(choices=ROLES_CHOICES)

    class Meta:
        unique_together = ('user', 'course')


class Environment(models.Model):
    PROCESSING = 0
    CREATED = 1
    FAILED = 2

    STATUS_CHOICES = (
        (PROCESSING, 'processing'),
        (CREATED, 'created'),
        (FAILED, 'failed'),
    )

    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='environments')
    tag = models.CharField(max_length=100, unique=True)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=0)
    dockerfile_content = models.TextField()

    def save(self, *args, **kwargs):
        pk = self.pk

        if 'update_fields' in kwargs and 'dockerfile_content' in kwargs['update_fields']:
            self.status = self.PROCESSING
            update_docker_image.delay(self.tag, self.id)

        super().save(*args, **kwargs)

        # Avoiding recursion provoked by calling `save` in create_docker_image task.
        if pk is None:
            create_docker_image.delay(self.id)

    def delete(self, *args, **kwargs):
        delete_docker_image.delay(self.tag)
        super().delete(*args, **kwargs)

    def __str__(self):
        if self.status == self.PROCESSING:
            return f'Processing \'{self.title}\''

        return f'{self.tag}: {self.title}'


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()

    def add_rule(self, title, description, order, command, timeout, continue_on_fail):
        from build_rules.models import Rule

        return Rule.objects.create(
            title=title,
            description=description,
            order=order,
            command=command,
            timeout=timeout,
            continue_on_fail=continue_on_fail,
            assignment=self
        )

    def remove_rule(self, rule_id):
        from build_rules.models import Rule

        Rule.objects.get(pk=rule_id).delete()

    def __str__(self):
        return self.title
