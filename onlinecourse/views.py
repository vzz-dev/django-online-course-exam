import logging
from typing import TYPE_CHECKING

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, User
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from typing_extensions import override

# <HINT> Import any new Models here
from .models import Choice, Course, Enrollment, Question, Submission

if TYPE_CHECKING:
    _CourseListViewBase = generic.ListView[Course]
    _CourseDetailViewBase = generic.DetailView[Course]
else:
    _CourseListViewBase = generic.ListView
    _CourseDetailViewBase = generic.DetailView

# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request: HttpRequest):
    context: dict[str, str] = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            _ = User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    else:
        return HttpResponseNotAllowed(["GET", "POST"])


def login_request(request: HttpRequest):
    context: dict[str, str] = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request: HttpRequest):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user: AbstractBaseUser | AnonymousUser, course: Course) -> bool:
    is_enrolled = False
    if user.pk is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(_CourseListViewBase):
    template_name: str | None = 'onlinecourse/course_list_bootstrap.html'
    context_object_name: str | None = 'course_list'

    @override
    def get_queryset(self) -> QuerySet[Course]:
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(_CourseDetailViewBase):
    model: type[Course] = Course
    template_name: str | None = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request: HttpRequest, course_id: int) -> HttpResponseRedirect:
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        _ = Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Get user and course object, then get the associated enrollment object created when the user enrolled the course
         # Create a submission object referring to the enrollment
         # Collect the selected choices from exam form
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id

def submit(request: HttpRequest, course_id: int) :
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    choices = extract_answers(request)

    submission.choices.set(choices)
    submission_id = submission.id

    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course_id, submission_id,)))

# An example method to collect the selected choices from the exam form from the request object
def extract_answers(request: HttpRequest) -> list[int]:
   submitted_answers: list[int] = []
   for key in request.POST:
       if key.startswith('choice'):
           value = request.POST[key]
           choice_id = int(value)
           submitted_answers.append(choice_id)
   return submitted_answers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
        # Get course and submission based on their ids
        # Get the selected choice ids from the submission record
        # For each selected choice, check if it is a correct answer or not
        # Calculate the total score
def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = Submission.objects.get(pk=submission_id)
    choices = submission.choices.all()

    total_score = 0
    questions = course.question_set.all()

    for question in questions:
        
        # Get all correct choices for the question
        correct_choices = question.choice_set.filter(is_correct=True) 
        # Get the user's selected choices for the question
        selected_choices =  choices.filter(question=question)

        # Check if the selected choices are the same as the correct choices
        if set(correct_choices) == set(selected_choices):
            total_score += question.score

    
    context['course'] = course
    context['total_score'] = total_score
    context['choices'] = choices

    return render(request, "onlinecourse/exam_result_bootstrap.html", context)
