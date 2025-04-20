from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, F, Q, Max
from django.forms import formset_factory, inlineformset_factory
from django.db.models.functions import TruncDate
import random
import time
import json
from datetime import timedelta
from django.contrib.auth import get_user_model


User = get_user_model()

from Courses.models import Course, Enrollment
from user.views import soc_user_required, non_soc_user_required
from .models import AwarenessModule, Question, Answer, ModuleAttempt, UserResponse
from .forms import AwarenessModuleForm, QuestionForm, AnswerForm, AIQuestionGenerationForm
from .utils import generate_awareness_questions, validate_generated_questions

# SOC user views for managing awareness modules
@login_required
@soc_user_required
def module_list(request):
    """List all awareness modules created by the user"""
    modules = AwarenessModule.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Add stats to each module
    for module in modules:
        module.attempt_count = ModuleAttempt.objects.filter(module=module).count()
        module.pass_count = ModuleAttempt.objects.filter(module=module, passed=True).count()
        if module.attempt_count > 0:
            module.pass_rate = (module.pass_count / module.attempt_count) * 100
        else:
            module.pass_rate = 0
    
    return render(request, 'Awareness/module_list.html', {'modules': modules})

@login_required
@soc_user_required
def create_module(request):
    """Create a new awareness module"""
    if request.method == 'POST':
        form = AwarenessModuleForm(request.POST, user=request.user)
        if form.is_valid():
            module = form.save(commit=False)
            module.created_by = request.user
            module.save()
            messages.success(request, f"Awareness module '{module.title}' created successfully.")
            return redirect('awareness:manage_questions', module_id=module.id)
    else:
        form = AwarenessModuleForm(user=request.user)
    
    return render(request, 'Awareness/create_module.html', {'form': form})

@login_required
@soc_user_required
def module_detail(request, module_id):
    """View details of an awareness module"""
    module = get_object_or_404(AwarenessModule, id=module_id, created_by=request.user)
    questions = Question.objects.filter(module=module).order_by('course_module_number')
    
    # Get analytics
    attempt_count = ModuleAttempt.objects.filter(module=module).count()
    pass_count = ModuleAttempt.objects.filter(module=module, passed=True).count()
    pass_rate = (pass_count / attempt_count * 100) if attempt_count > 0 else 0
    avg_score = ModuleAttempt.objects.filter(module=module).aggregate(Avg('score'))['score__avg'] or 0
    
    context = {
        'module': module,
        'questions': questions,
        'attempt_count': attempt_count,
        'pass_count': pass_count,
        'pass_rate': pass_rate,
        'avg_score': avg_score
    }
    return render(request, 'Awareness/module_detail.html', context)

@login_required
@soc_user_required
def edit_module(request, module_id):
    """Edit an existing awareness module"""
    module = get_object_or_404(AwarenessModule, id=module_id, created_by=request.user)
    
    if request.method == 'POST':
        form = AwarenessModuleForm(request.POST, instance=module, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Awareness module '{module.title}' updated successfully.")
            return redirect('awareness:module_detail', module_id=module.id)
    else:
        form = AwarenessModuleForm(instance=module, user=request.user)
    
    return render(request, 'Awareness/edit_module.html', {'form': form, 'module': module})

@login_required
@soc_user_required
def delete_module(request, module_id):
    """Delete an awareness module"""
    module = get_object_or_404(AwarenessModule, id=module_id, created_by=request.user)
    
    if request.method == 'POST':
        module_title = module.title
        module.delete()
        messages.success(request, f"Awareness module '{module_title}' deleted successfully.")
        return redirect('awareness:module_list')
    
    return render(request, 'Awareness/delete_module.html', {'module': module})

@login_required
@soc_user_required
def manage_questions(request, module_id):
    """Manage questions for an awareness module"""
    module = get_object_or_404(AwarenessModule, id=module_id, created_by=request.user)
    questions = Question.objects.filter(module=module).order_by('course_module_number')
    
    # Get course modules for reference
    course_modules = module.course.modules.all().order_by('order')
    
    # Create a set of module numbers that have questions
    module_questions_count = set(questions.values_list('course_module_number', flat=True))
    
    context = {
        'module': module,
        'questions': questions,
        'course_modules': course_modules,
        'module_questions_count': module_questions_count,
    }
    return render(request, 'Awareness/manage_questions.html', context)

@login_required
@soc_user_required
def add_question(request, module_id):
    """Add a new question to an awareness module"""
    module = get_object_or_404(AwarenessModule, id=module_id, created_by=request.user)
    AnswerFormSet = formset_factory(AnswerForm, extra=4)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_formset = AnswerFormSet(request.POST, prefix='answers')
        
        if question_form.is_valid() and answer_formset.is_valid():
            question = question_form.save(commit=False)
            question.module = module
            question.save()
            
            # Process and save answers
            for form in answer_formset:
                if form.cleaned_data and form.cleaned_data.get('text'):
                    answer = form.save(commit=False)
                    answer.question = question
                    answer.save()
            
            messages.success(request, "Question added successfully.")
            return redirect('awareness:manage_questions', module_id=module.id)
    else:
        question_form = QuestionForm()
        answer_formset = AnswerFormSet(prefix='answers')
    
    # Get course modules for reference
    course_modules = module.course.modules.all().order_by('order')
    
    context = {
        'module': module,
        'question_form': question_form,
        'answer_formset': answer_formset,
        'course_modules': course_modules,
    }
    return render(request, 'Awareness/add_question.html', context)

@login_required
@soc_user_required
def edit_question(request, question_id):
    """View for editing an existing question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Create the formset for answers
    AnswerFormSet = inlineformset_factory(
        Question, 
        Answer, 
        form=AnswerForm, 
        extra=0, 
        can_delete=True,
        min_num=2,
        validate_min=True
    )
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        answer_formset = AnswerFormSet(request.POST, instance=question)
        
        if question_form.is_valid() and answer_formset.is_valid():
            question_form.save()
            answer_formset.save()
            
            # Check if at least one answer is marked as correct
            has_correct_answer = any(
                form.cleaned_data.get('is_correct')
                for form in answer_formset.forms
                if not form.cleaned_data.get('DELETE', False)
            )
            
            if not has_correct_answer:
                answer_formset.non_form_errors = ["At least one answer must be marked as correct."]
                return render(request, 'Awareness/edit_question.html', {
                    'question': question,
                    'question_form': question_form,
                    'answer_formset': answer_formset,
                    'error': "At least one answer must be marked as correct."
                })
            
            return redirect('awareness:manage_questions', module_id=question.module.id)
    else:
        question_form = QuestionForm(instance=question)
        answer_formset = AnswerFormSet(instance=question)
    
    return render(request, 'Awareness/edit_question.html', {
        'question': question,
        'question_form': question_form,
        'answer_formset': answer_formset
    })

@login_required
@soc_user_required
def delete_question(request, question_id):
    """View for deleting a question"""
    question = get_object_or_404(Question, id=question_id)
    module_id = question.module.id
    
    # Optional: add permission check here
    
    if request.method == 'POST':
        question.delete()
        return redirect('awareness:manage_questions', module_id=module_id)
    
    # For GET requests, show a confirmation page
    return render(request, 'Awareness/delete_question_confirm.html', {
        'question': question
    })

@login_required
@soc_user_required
def generate_questions(request, module_id):
    """Generate questions with AI assistance"""
    module = get_object_or_404(AwarenessModule, id=module_id, created_by=request.user)
    course = module.course
    
    if request.method == 'POST':
        form = AIQuestionGenerationForm(request.POST)
        if form.is_valid():
            use_ai = form.cleaned_data['use_ai']
            additional_context = form.cleaned_data.get('additional_context', '')
            
            if use_ai:
                # Use our new AI utility to generate questions
                result = generate_awareness_questions(module, additional_context)
                
                # Validate the generated questions
                is_valid, errors = validate_generated_questions(result)
                
                if not is_valid:
                    for error in errors:
                        messages.error(request, error)
                    return redirect('awareness:generate_questions', module_id=module.id)
                    
                # Process and save the questions
                questions_created = 0
                
                for question_data in result.get('questions', []):
                    try:
                        # Create the question
                        question = Question(
                            module=module,
                            text=question_data['text'],
                            question_type=question_data['question_type'],
                            course_module_number=question_data['module_number'],
                            explanation=question_data.get('explanation', '')
                        )
                        question.save()
                        
                        # Create the answers
                        for answer_data in question_data.get('answers', []):
                            Answer.objects.create(
                                question=question,
                                text=answer_data['text'],
                                is_correct=answer_data['is_correct'],
                                explanation=answer_data.get('explanation', '')
                            )
                            
                        questions_created += 1
                    except Exception as e:
                        messages.error(request, f"Error creating question: {str(e)}")
                
                if questions_created > 0:
                    messages.success(request, f"Successfully created {questions_created} questions.")
                else:
                    messages.warning(request, "No questions were created. Please try again.")
                
                return redirect('awareness:manage_questions', module_id=module.id)
            else:
                # Create basic placeholder questions as before
                course_modules = course.modules.all().order_by('order')
                
                for i, course_module in enumerate(course_modules):
                    # Create a question for this module
                    question = Question(
                        module=module,
                        text=f"This is an auto-generated question about {course_module.title}",
                        question_type='single',
                        course_module_number=i,
                        explanation=f"Explanation for content from {course_module.title}"
                    )
                    question.save()
                    
                    # Create some answers
                    Answer.objects.create(
                        question=question,
                        text="Correct answer",
                        is_correct=True,
                        explanation="This is the right answer because..."
                    )
                    
                    for j in range(3):
                        Answer.objects.create(
                            question=question,
                            text=f"Incorrect answer option {j+1}",
                            is_correct=False,
                            explanation=f"This is wrong because..."
                        )
                
                messages.success(request, f"{course_modules.count()} questions generated successfully.")
                return redirect('awareness:manage_questions', module_id=module.id)
    else:
        form = AIQuestionGenerationForm()
    
    return render(request, 'Awareness/generate_questions.html', {
        'form': form,
        'module': module,
        'course': course
    })

# User-facing views for taking awareness modules
@login_required
def take_module(request, module_id):
    """View an awareness module"""
    module = get_object_or_404(AwarenessModule, id=module_id)
    
    # Check if the user has completed the associated course
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=module.course)
        course_completed = enrollment.completed
    except Enrollment.DoesNotExist:
        enrollment = None
        course_completed = False
    
    if not course_completed:
        messages.warning(request, f"You need to complete the course '{module.course.title}' before taking this awareness module.")
        return redirect('courses:course_list')
    
    # Check if user has any ongoing attempts
    ongoing_attempt = ModuleAttempt.objects.filter(
        user=request.user, 
        module=module, 
        passed=False
    ).first()
    
    # Check if the user has completed this module and get the latest passed attempt
    passed_attempt = ModuleAttempt.objects.filter(
        user=request.user,
        module=module,
        passed=True
    ).order_by('-attempt_date').first()
    
    has_passed = passed_attempt is not None
    
    context = {
        'module': module,
        'enrollment': enrollment,
        'ongoing_attempt': ongoing_attempt,
        'has_passed': has_passed,
        'passed_attempt': passed_attempt  # This could be None, but we'll handle it in the template
    }
    return render(request, 'Awareness/take_module.html', context)

@login_required
def start_module(request, module_id):
    """Start a new attempt at an awareness module"""
    module = get_object_or_404(AwarenessModule, id=module_id)
    
    # Check if the user has completed the associated course
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=module.course)
        course_completed = enrollment.completed
    except Enrollment.DoesNotExist:
        messages.warning(request, "You need to enroll in the course first.")
        return redirect('courses:course_list')
    
    if not course_completed:
        messages.warning(request, f"You need to complete the course '{module.course.title}' before taking this awareness module.")
        return redirect('courses:course_detail', course_id=module.course.id)
    
    # Create a new attempt
    attempt = ModuleAttempt.objects.create(
        user=request.user,
        module=module,
        score=0,
        passed=False
    )
    
    # Get all questions for this module
    all_questions = Question.objects.filter(module=module)
    
    # Get previously seen questions in failed attempts
    seen_questions = set()
    for previous_attempt in ModuleAttempt.objects.filter(
        user=request.user, 
        module=module, 
        passed=False
    ).exclude(id=attempt.id):
        seen_questions.update(previous_attempt.questions_seen.values_list('id', flat=True))
    
    # Prioritize unseen questions
    unseen_questions = all_questions.exclude(id__in=seen_questions)
    
    # Select 5 questions (or fewer if not enough available)
    # Try to get one from each course module if possible
    selected_questions = []
    course_modules = module.course.modules.all().order_by('order')
    
    for i, _ in enumerate(course_modules):
        module_questions = unseen_questions.filter(course_module_number=i)
        if module_questions.exists():
            selected_questions.append(random.choice(module_questions))
        else:
            # If no unseen questions for this module, try seen ones
            module_questions = all_questions.filter(course_module_number=i)
            if module_questions.exists():
                selected_questions.append(random.choice(module_questions))
    
    # If we still don't have 5 questions, add random ones
    while len(selected_questions) < min(5, all_questions.count()):
        remaining_questions = all_questions.exclude(id__in=[q.id for q in selected_questions])
        if not remaining_questions.exists():
            break
        selected_questions.append(random.choice(remaining_questions))
    
    # Save the selected questions to the attempt
    attempt.questions_seen.set(selected_questions)
    
    # Store questions in session
    request.session['current_attempt_id'] = attempt.id
    request.session['question_ids'] = [q.id for q in selected_questions]
    request.session['start_time'] = time.time()
    
    return redirect('awareness:complete_module', module_id=module.id)

@login_required
def complete_module(request, module_id):
    """Complete an ongoing module attempt"""
    module = get_object_or_404(AwarenessModule, id=module_id)
    
    # Get attempt from session
    attempt_id = request.session.get('current_attempt_id')
    if not attempt_id:
        messages.error(request, "No active awareness module attempt found.")
        return redirect('awareness:take_module', module_id=module.id)
    
    attempt = get_object_or_404(ModuleAttempt, id=attempt_id, user=request.user)
    question_ids = request.session.get('question_ids', [])
    questions = Question.objects.filter(id__in=question_ids)
    
    if request.method == 'POST':
        score = 0
        
        # Process each question
        for question in questions:
            is_correct = False
            
            if question.is_multiple_choice():
                # For multiple choice questions
                correct_answers = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
                selected_answers = set([int(x) for x in request.POST.getlist(f'question_{question.id}', [])])
                is_correct = correct_answers == selected_answers
            else:
                # For single choice questions
                try:
                    selected_answer_id = int(request.POST.get(f'question_{question.id}', 0))
                    is_correct = question.answers.filter(id=selected_answer_id, is_correct=True).exists()
                except (ValueError, TypeError):
                    is_correct = False
            
            # Save user's response
            response = UserResponse.objects.create(
                attempt=attempt,
                question=question,
                is_correct=is_correct
            )
            
            # Add selected answers to the response
            if question.is_multiple_choice():
                selected_ids = request.POST.getlist(f'question_{question.id}', [])
                response.selected_answers.set(selected_ids)
            else:
                selected_id = request.POST.get(f'question_{question.id}')
                if selected_id:
                    response.selected_answers.add(selected_id)
            
            if is_correct:
                score += 1
        
        # Calculate time taken
        start_time = request.session.get('start_time')
        if start_time:
            time_taken = int(time.time() - start_time)
            attempt.time_taken = time_taken
        
        # Update attempt
        attempt.score = score
        attempt.passed = score >= 3  # Pass threshold is 3 out of 5
        attempt.save()
        
        # Clear session data
        if 'current_attempt_id' in request.session:
            del request.session['current_attempt_id']
        if 'question_ids' in request.session:
            del request.session['question_ids']
        if 'start_time' in request.session:
            del request.session['start_time']
        
        # Award points if passed
        if attempt.passed:
            # Implement point awarding logic here
            point_value = module.get_point_value()
            # Update user's points or send to a reward system
            
            messages.success(request, f"Congratulations! You passed the awareness module with a score of {score}/5 and earned {point_value} points!")
            return redirect('awareness:review_attempt', attempt_id=attempt.id)
        else:
            messages.warning(request, f"You scored {score}/5. You need at least 3 correct answers to pass. Please try again.")
            return redirect('awareness:take_module', module_id=module.id)
    
    context = {
        'module': module,
        'attempt': attempt,
        'questions': questions
    }
    return render(request, 'Awareness/complete_module.html', context)

@login_required
def review_attempt(request, attempt_id):
    """Review a passed module attempt"""
    attempt = get_object_or_404(ModuleAttempt, id=attempt_id, user=request.user)
    
    # Only allow reviewing passed attempts
    if not attempt.passed:
        messages.warning(request, "You can only review passed attempts.")
        return redirect('awareness:take_module', module_id=attempt.module.id)
    
    # Get responses with questions and selected answers
    responses = UserResponse.objects.filter(attempt=attempt).select_related('question')
    
    context = {
        'attempt': attempt,
        'module': attempt.module,
        'responses': responses
    }
    return render(request, 'Awareness/review_attempt.html', context)

# Analytics views
@login_required
@soc_user_required
def module_analytics(request):
    """View analytics for all modules"""
    modules = AwarenessModule.objects.filter(created_by=request.user)
    
    # Calculate overall stats
    total_attempts = ModuleAttempt.objects.filter(module__in=modules).count()
    total_passes = ModuleAttempt.objects.filter(module__in=modules, passed=True).count()
    pass_rate = (total_passes / total_attempts * 100) if total_attempts > 0 else 0
    
    # Get stats per module
    module_stats = []
    for module in modules:
        attempts = ModuleAttempt.objects.filter(module=module)
        passes = attempts.filter(passed=True).count()
        stats = {
            'module': module,
            'attempts': attempts.count(),
            'passes': passes,
            'pass_rate': (passes / attempts.count() * 100) if attempts.count() > 0 else 0,
            'avg_score': attempts.aggregate(Avg('score'))['score__avg'] or 0,
            'avg_time': attempts.aggregate(Avg('time_taken'))['time_taken__avg'] or 0,
        }
        module_stats.append(stats)
    
    context = {
        'total_attempts': total_attempts,
        'total_passes': total_passes,
        'pass_rate': pass_rate,
        'module_stats': module_stats
    }
    return render(request, 'Awareness/module_analytics.html', context)

@login_required
@soc_user_required
def module_detail_analytics(request, module_id):
    """View for module analytics dashboard"""
    module = get_object_or_404(AwarenessModule, id=module_id)
    
    # Basic statistics
    all_attempts = ModuleAttempt.objects.filter(module=module)
    total_attempts = all_attempts.count()
    
    # Pass rate
    passed_attempts = all_attempts.filter(passed=True).count()
    pass_rate = round((passed_attempts / total_attempts) * 100) if total_attempts > 0 else 0
    
    # Average score
    avg_score = round(all_attempts.aggregate(Avg('score'))['score__avg'] or 0)
    
    # Unique users
    unique_users = all_attempts.values('user').distinct().count()
    
    # Score distribution (0-20%, 21-40%, etc.)
    score_distribution = [
        all_attempts.filter(score__lte=20).count(),
        all_attempts.filter(score__gt=20, score__lte=40).count(),
        all_attempts.filter(score__gt=40, score__lte=60).count(),
        all_attempts.filter(score__gt=60, score__lte=80).count(),
        all_attempts.filter(score__gt=80).count(),
    ]
    
    # Attempts over time (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    attempts_by_day = all_attempts.filter(
        attempt_date__gte=thirty_days_ago
    ).annotate(
        day=TruncDate('attempt_date')
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Format for chart.js
    day_labels = []
    day_counts = []
    
    # Create a complete date range for the last 30 days
    date_range = [thirty_days_ago.date() + timedelta(days=x) for x in range(31)]
    data_dict = {item['day']: item['count'] for item in attempts_by_day}
    
    for date in date_range:
        day_labels.append(date.strftime("%b %d"))
        day_counts.append(data_dict.get(date, 0))
    
    # Question performance
    questions = module.questions.all()
    question_stats = []
    
    for question in questions:
        # Get responses for this question
        responses = UserResponse.objects.filter(
            question=question,
            attempt__module=module
        )
        total_responses = responses.count()
        correct_responses = responses.filter(is_correct=True).count()
        
        correct_percentage = round((correct_responses / total_responses) * 100) if total_responses > 0 else 0
        
        question_stats.append({
            'text': question.text,
            'total_responses': total_responses,
            'correct_responses': correct_responses,
            'correct_percentage': correct_percentage
        })
    
    # Sort questions by correctness rate (ascending)
    question_stats = sorted(question_stats, key=lambda x: x['correct_percentage'])
    
    # Top performers
    top_performers = []
    top_users = all_attempts.filter(
        passed=True
    ).values(
        'user'
    ).annotate(
        max_score=Max('score'),
        attempts=Count('id')
    ).order_by('-max_score')[:5]
    
    for entry in top_users:
        user = User.objects.get(id=entry['user'])
        top_performers.append({
            'username': user.username,
            'get_full_name': user.username,
            'score': entry['max_score'],
            'attempts': entry['attempts']
        })
    
    # Time to complete
    attempts_with_time = all_attempts.exclude(time_taken__isnull=True)
    avg_time_seconds = attempts_with_time.aggregate(Avg('time_taken'))['time_taken__avg'] or 0
    avg_time_mins = round(avg_time_seconds / 60, 1)
    
    # Completion time distribution
    completion_time_data = [
        attempts_with_time.filter(time_taken__lt=300).count(),  # < 5 min
        attempts_with_time.filter(time_taken__gte=300, time_taken__lt=600).count(),  # 5-10 min
        attempts_with_time.filter(time_taken__gte=600, time_taken__lt=900).count(),  # 10-15 min
        attempts_with_time.filter(time_taken__gte=900).count(),  # > 15 min
    ]
    
    # Recent activity
    recent_attempts = all_attempts.select_related('user').order_by('-attempt_date')[:5]
    
    return render(request, 'Awareness/module_detail_analytics.html', {
        'module': module,
        'total_attempts': total_attempts,
        'pass_rate': pass_rate,
        'avg_score': avg_score,
        'unique_users': unique_users,
        'score_distribution': json.dumps(score_distribution),
        'time_labels': json.dumps(day_labels),
        'time_data': json.dumps(day_counts),
        'question_stats': question_stats,
        'top_performers': top_performers,
        'avg_time_mins': avg_time_mins,
        'completion_time_data': json.dumps(completion_time_data),
        'recent_attempts': recent_attempts
    })
