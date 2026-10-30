from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, cast

from typing_extensions import override

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now


# Instructor model
class Instructor(models.Model):
    user: models.ForeignKey[AbstractUser, AbstractUser] = models.ForeignKey(
        cast(str, settings.AUTH_USER_MODEL),
        on_delete=models.CASCADE,
    )
    full_time: models.BooleanField[bool, bool] = models.BooleanField(default=True)
    total_learners: models.IntegerField[int, int] = models.IntegerField()

    @override
    def __str__(self):
        return self.user.username


# Learner model
class Learner(models.Model):
    user: models.ForeignKey[AbstractUser, AbstractUser] = models.ForeignKey(
        cast(str, settings.AUTH_USER_MODEL),
        on_delete=models.CASCADE,
    )
    STUDENT: str = 'student'
    DEVELOPER: str = 'developer'
    DATA_SCIENTIST: str = 'data_scientist'
    DATABASE_ADMIN: str = 'dba'
    OCCUPATION_CHOICES: list[tuple[str, str]] = [
        (STUDENT, 'Student'),
        (DEVELOPER, 'Developer'),
        (DATA_SCIENTIST, 'Data Scientist'),
        (DATABASE_ADMIN, 'Database Admin')
    ]
    occupation: models.CharField[str, str] = models.CharField(
        null=False,
        max_length=20,
        choices=OCCUPATION_CHOICES,
        default=STUDENT
    )
    social_link: models.URLField[str, str] = models.URLField(max_length=200)

    @override
    def __str__(self):
        return self.user.username + "," + \
               self.occupation


# Course model
class Course(models.Model):
    name: models.CharField[str, str] = models.CharField(null=False, max_length=30, default='online course')
    image: models.ImageField = models.ImageField(upload_to='course_images/')
    description: models.CharField[str, str] = models.CharField(max_length=1000)
    pub_date: models.DateField[date | str | None, date | None] = models.DateField(null=True)
    instructors: models.ManyToManyField[Instructor, models.Model] = models.ManyToManyField(Instructor)
    users: models.ManyToManyField[AbstractUser, "Enrollment"] = models.ManyToManyField(
        cast(str, settings.AUTH_USER_MODEL),
        through='Enrollment'
    )
    total_enrollment: models.IntegerField[int, int] = models.IntegerField(default=0)
    is_enrolled: bool = False

    if TYPE_CHECKING:
        @property
        def question_set(self) -> RelatedManager["Question"]: ... # type: ignore

    @override
    def __str__(self):
        return "Name: " + self.name + "," + \
               "Description: " + self.description


# Lesson model
class Lesson(models.Model):
    title: models.CharField[str, str] = models.CharField(max_length=200, default="title")
    order: models.IntegerField[int, int] = models.IntegerField(default=0)
    course: models.ForeignKey[Course, Course] = models.ForeignKey(Course, on_delete=models.CASCADE)
    content: models.TextField[str, str] = models.TextField()


# Enrollment model
# <HINT> Once a user enrolled a class, an enrollment entry should be created between the user and course
# And we could use the enrollment to track information such as exam submissions
class Enrollment(models.Model):
    AUDIT: str = 'audit'
    HONOR: str = 'honor'
    BETA: str = 'BETA'
    COURSE_MODES: list[tuple[str, str]] = [
        (AUDIT, 'Audit'),
        (HONOR, 'Honor'),
        (BETA, 'BETA')
    ]
    user: models.ForeignKey[AbstractUser, AbstractUser] = models.ForeignKey(
        cast(str, settings.AUTH_USER_MODEL),
        on_delete=models.CASCADE
    )
    course: models.ForeignKey[Course, Course] = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled: models.DateField[date | str, date] = models.DateField(default=now)
    mode: models.CharField[str, str] = models.CharField(max_length=5, choices=COURSE_MODES, default=AUDIT)
    rating: models.FloatField[float, float] = models.FloatField(default=5.0)


# Question model
class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_text: models.CharField[str, str] = models.CharField(max_length=200)
    score: models.IntegerField[int, int] = models.IntegerField(default=50)

    if TYPE_CHECKING:
        @property
        def choice_set(self) -> RelatedManager["Choice"]: ...

    @override
    def __str__(self):
        return "Question: " + self.question_text

    # method to calculate if the learner gets the score of the question
    def is_get_score(self, selected_ids: list[int]) -> bool:
        correct_ids = set(
            self.choice_set.filter(is_correct=True).values_list("id", flat=True)
        )
        return correct_ids == set(selected_ids)

# Choice model
class Choice(models.Model):
    question: models.ForeignKey[Question, Question] = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text: models.CharField[str, str] = models.CharField(max_length=200)
    is_correct: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    @override
    def __str__(self):
        return self.choice_text

# One enrollment could have multiple submission
# One submission could have multiple choices
# One choice could belong to multiple submissions
class Submission(models.Model):
   enrollment: models.ForeignKey[Enrollment, Enrollment] = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
   choices: models.ManyToManyField[Choice, models.Model] = models.ManyToManyField(Choice)

   @override
   def __str__(self):
       return f"Submission {self.pk}"
