import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Prefetch, Avg
from django.forms import inlineformset_factory
from django.db.models.functions import TruncMonth
from datetime import timedelta
from django.contrib.auth import get_user_model


User = get_user_model()

from .models import (
    Course, 
    Module, 
    Chapter, 
    Question, 
    Choice, 
    Enrollment, 
    Progress, 
    CourseEvaluation,
    CourseCreationSession,
    SessionMessage,
    DocumentContext,
    CompletedModule
)
from .forms import (
    CourseForm, 
    ModuleForm, 
    ChapterForm, 
    QuestionForm, 
    ChoiceForm, 
    CourseInitialPromptForm, 
    CoursePromptForm,
    CourseEvaluationForm,
    QuizForm
)
from .utils import (
    generate_course_structure, 
    generate_chapters, 
    generate_chapter_content,
    extract_text_from_document
)

def is_soc_user(user):
    """Check if user is a SOC user"""
    return user.is_authenticated and user.user_type == 'soc'

# Custom decorator for SOC user access
def soc_required(view_func):
    """Decorator to ensure only SOC members can access certain views"""
    def wrapped(request, *args, **kwargs):
        if not is_soc_user(request.user):
            messages.error(request, "Access denied. SOC membership required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped

@login_required
def course_list(request):
    # Start with all courses
    if request.user.user_type == 'soc':
        # SOC users can see all courses
        courses = Course.objects.all()
    else:
        # Non-SOC users can only see awareness courses
        courses = Course.objects.filter(course_type='awareness')
    
    # Filter by course type if specified
    course_type = request.GET.get('type')
    if course_type:
        courses = courses.filter(course_type=course_type)
    
    # Filter by search term if specified
    search = request.GET.get('search')
    if search:
        courses = courses.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    # Filter by enrollment status if specified
    enrolled = request.GET.get('enrolled') == 'true'
    if enrolled:
        user_enrollments = request.user.course_enrollments.values_list('course', flat=True)
        courses = courses.filter(id__in=user_enrollments)
    
    # Mark courses that the user is enrolled in
    enrolled_courses = request.user.course_enrollments.values_list('course', flat=True)
    for course in courses:
        course.is_enrolled = course.id in enrolled_courses
    
    context = {
        'courses': courses,
        'is_soc_user': request.user.user_type == 'soc'
    }
    return render(request, 'courses/course_list.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all().order_by('order')
    
    # Calculate total chapters for display
    total_chapters = Chapter.objects.filter(module__course=course).count()
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
        already_enrolled = True
    except Enrollment.DoesNotExist:
        already_enrolled = False
        enrollment = None
    
    context = {
        'course': course,
        'modules': modules,
        'already_enrolled': already_enrolled,
        'enrollment': enrollment,
        'total_chapters': total_chapters  # Pass total_chapters separately in the context
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def module_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    
    # Check if user is enrolled in the course
    try:
        course = module.course
        enrollment = Enrollment.objects.get(user=request.user, course=course)
    except Enrollment.DoesNotExist:
        return redirect('courses:course_detail', course_id=module.course.id)
    
    # Check if this module is completed
    is_completed = CompletedModule.objects.filter(user=request.user, module=module).exists()
    
    context = {
        'module': module,
        'is_completed': is_completed
    }
    return render(request, 'courses/module_detail.html', context)

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        enrollment = Enrollment.objects.create(user=request.user, course=course)
        
        # Create progress records for each chapter
        chapters = Chapter.objects.filter(module__course=course)
        for chapter in chapters:
            Progress.objects.create(
                enrollment=enrollment,
                chapter=chapter
            )
    
    # Use the correct URL pattern name with the namespace
    return redirect('courses:course_detail', course_id=course.id)

@login_required
def course_enroll(request, pk):
    course = get_object_or_404(Course, id=pk)
    
    # Check if already enrolled
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        Enrollment.objects.create(user=request.user, course=course)
        
        # Create progress records for each chapter
        chapters = Chapter.objects.filter(module__course=course)
        for chapter in chapters:
            Progress.objects.create(
                enrollment=Enrollment.objects.get(user=request.user, course=course),
                chapter=chapter
            )
    
    return redirect('courses:course_detail', course_id=course.id)

@login_required
def complete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    
    # Check if user is enrolled in the course
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=module.course)
    except Enrollment.DoesNotExist:
        return redirect('course_detail', course_id=module.course.id)
    
    # Mark module as completed if not already completed
    if not CompletedModule.objects.filter(user=request.user, module=module).exists():
        CompletedModule.objects.create(user=request.user, module=module)
        
        # Update course progress
        total_modules = module.course.modules.count()
        completed_modules = CompletedModule.objects.filter(
            user=request.user, 
            module__course=module.course
        ).count()
        
        enrollment.progress = int((completed_modules / total_modules) * 100)
        if enrollment.progress == 100:
            enrollment.completed = True
        enrollment.save()
    
    return redirect('course_detail', course_id=module.course.id)

@login_required
def my_courses(request):
    """View user's enrolled courses"""
    user = request.user
    enrollments = Enrollment.objects.filter(user=user).select_related('course')
    
    # Calculate progress for each enrollment
    for enrollment in enrollments:
        total_chapters = Progress.objects.filter(enrollment=enrollment).count()
        completed_chapters = Progress.objects.filter(enrollment=enrollment, completed=True).count()
        
        if total_chapters > 0:
            enrollment.progress_percentage = (completed_chapters / total_chapters) * 100
        else:
            enrollment.progress_percentage = 0
    
    context = {
        'enrollments': enrollments,
    }
    return redirect('/courses/?enrolled=true')

@login_required
def course_learn(request, enrollment_id):
    """Main learning view for an enrolled course"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
    course = enrollment.course
    
    # Find the first incomplete chapter, or the first chapter if none are complete
    try:
        progress = Progress.objects.filter(
            enrollment=enrollment, 
            completed=False
        ).select_related('chapter').order_by('chapter__module__order', 'chapter__order').first()
        
        if progress:
            # Found incomplete chapter
            current_chapter = progress.chapter
        else:
            # All chapters are complete - go to the first chapter
            current_chapter = Chapter.objects.filter(
                module__course=course
            ).order_by('module__order', 'order').first()
            
    except Exception:
        # Fallback to first chapter
        current_chapter = Chapter.objects.filter(
            module__course=course
        ).order_by('module__order', 'order').first()
    
    if current_chapter:
        # Ensure progress record exists (create if not)
        progress, created = Progress.objects.get_or_create(
            enrollment=enrollment,
            chapter=current_chapter,
            defaults={'completed': False}
        )
        
        # Update enrollment progress value
        total_chapters = Progress.objects.filter(enrollment=enrollment).count()
        completed_chapters = Progress.objects.filter(enrollment=enrollment, completed=True).count()
        
        if total_chapters > 0:
            enrollment.progress_value = round((completed_chapters / total_chapters) * 100)
            enrollment.save()
        
        return redirect('courses:chapter_view', chapter_id=current_chapter.id)
    else:
        messages.error(request, "No chapters found in this course.")
        return redirect('courses:course_list')

@login_required
def chapter_view(request, chapter_id):
    """View a specific chapter and its quiz"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    module = chapter.module
    course = module.course
    
    # Check if user is enrolled in this course
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You need to enroll in this course first.")
        return redirect('courses:course_detail', course_id=course.id)
    
    # Get progress for this chapter
    progress, created = Progress.objects.get_or_create(
        enrollment=enrollment,
        chapter=chapter
    )
    
    # Automatically mark summary chapters as completed when viewed
    if chapter.is_summary and not progress.completed:
        progress.completed = True
        progress.completed_date = timezone.now()
        progress.save()
    
    # Check if this is the final chapter and update enrollment status
    is_final_chapter = not Chapter.objects.filter(
        module__course=course,
        module__order__gte=module.order,
        order__gt=chapter.order if module.order == module.order else 0
    ).exists()
    
    if is_final_chapter and (progress.completed or chapter.is_summary):
        # Check if all chapters are completed
        all_chapters = Chapter.objects.filter(module__course=course).count()
        completed_chapters = Progress.objects.filter(
            enrollment=enrollment, 
            completed=True
        ).count()
        
        # Update progress percentage
        enrollment.progress_value = round((completed_chapters / all_chapters) * 100)
        
        # Mark as completed if all chapters are done
        if completed_chapters == all_chapters:
            enrollment.completed = True
            enrollment.completed_date = timezone.now()
            
        enrollment.save()
    
    # Group progress records to show the sidebar navigation
    all_progress = Progress.objects.filter(
        enrollment=enrollment
    ).select_related('chapter', 'chapter__module').order_by(
        'chapter__module__order', 'chapter__order'
    )
    
    # Group progress by module
    module_progress = {}
    for prog in all_progress:
        module_id = prog.chapter.module.id
        if module_id not in module_progress:
            module_progress[module_id] = {
                'module': prog.chapter.module,
                'chapters': []
            }
        module_progress[module_id]['chapters'].append(prog)
    
    # Create quiz form if this is not a summary chapter
    quiz_form = None
    if not chapter.is_summary and not progress.completed:
        quiz_form = QuizForm(chapter=chapter)
    
    # Find next and previous chapters
    all_chapters = list(Chapter.objects.filter(
        module__course=course
    ).order_by('module__order', 'order'))
    
    try:
        current_index = all_chapters.index(chapter)
        previous_chapter = all_chapters[current_index - 1] if current_index > 0 else None
        next_chapter = all_chapters[current_index + 1] if current_index < len(all_chapters) - 1 else None
    except (ValueError, IndexError):
        previous_chapter = None
        next_chapter = None
    
    context = {
        'chapter': chapter,
        'module': module,
        'course': course,
        'enrollment': enrollment,
        'progress': progress,
        'module_progress': module_progress,
        'quiz_form': quiz_form,
        'previous_chapter': previous_chapter,
        'next_chapter': next_chapter,
        'is_final_chapter': next_chapter is None
    }
    return render(request, 'courses/chapter_view.html', context)

@login_required
def submit_quiz(request, chapter_id):
    """Handle quiz submission for a chapter"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    module = chapter.module
    course = module.course
    
    # Check if user is enrolled in this course
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You need to enroll in this course first.")
        return redirect('courses:course_detail', course_id=course.id)
    
    # Get the progress for this chapter
    progress, created = Progress.objects.get_or_create(
        enrollment=enrollment, 
        chapter=chapter
    )
    
    # Don't allow submission if this is a summary or already completed
    if chapter.is_summary or progress.completed:
        return redirect('courses:chapter_view', chapter_id=chapter.id)
    
    if request.method == 'POST':
        quiz_form = QuizForm(chapter=chapter, data=request.POST)
        if quiz_form.is_valid():
            all_correct = True
            
            # Check each question
            for question in chapter.questions.all():
                field_name = f'question_{question.id}'
                if field_name in quiz_form.cleaned_data:
                    selected_choice_id = int(quiz_form.cleaned_data[field_name])
                    
                    # Check if the selected choice is correct
                    try:
                        selected_choice = Choice.objects.get(id=selected_choice_id, question=question)
                        if not selected_choice.is_correct:
                            all_correct = False
                            break
                    except Choice.DoesNotExist:
                        all_correct = False
                        break
                else:
                    all_correct = False
                    break
            
            if all_correct:
                # Mark chapter as complete
                progress.completed = True
                progress.completed_date = timezone.now()
                progress.save()
                
                messages.success(request, "Congratulations! You completed this chapter.")
                
                # Find the next chapter
                next_chapter = Chapter.objects.filter(
                    module__course=course,
                    module__order__gte=module.order,
                    order__gt=chapter.order if module.order == module.order else 0
                ).order_by('module__order', 'order').first()
                
                if next_chapter:
                    return redirect('courses:chapter_view', chapter_id=next_chapter.id)
                else:
                    # Mark course as complete if this was the last chapter
                    enrollment.completed = True
                    enrollment.completed_date = timezone.now()
                    enrollment.save()
                    return redirect('courses:evaluate_course', enrollment_id=enrollment.id)
            else:
                messages.error(request, "Some answers are incorrect. Please try again.")
        else:
            messages.error(request, "Please answer all questions before submitting.")
    
    return redirect('courses:chapter_view', chapter_id=chapter.id)

@login_required
def evaluate_course(request, enrollment_id):
    """Evaluate a completed course"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
    
    # Set enrollment as completed if not already
    if not enrollment.completed:
        enrollment.completed = True
        enrollment.completed_date = timezone.now()
        enrollment.save()
    
    # Check if evaluation already exists
    try:
        evaluation = CourseEvaluation.objects.get(enrollment=enrollment)
        messages.info(request, "You have already evaluated this course.")
        return redirect('courses:course_list')
    except CourseEvaluation.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = CourseEvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.enrollment = enrollment
            evaluation.save()
            
            messages.success(request, "Thank you for your feedback!")
            
            # Redirect to appropriate dashboard
            if is_soc_user(request.user):
                return redirect('soc_dashboard')
            else:
                return redirect('non_soc_dashboard')
    else:
        form = CourseEvaluationForm()
    
    context = {
        'form': form,
        'enrollment': enrollment
    }
    return render(request, 'courses/evaluate_course.html', context)

@login_required
@soc_required
def create_course_start(request):
    """Start the process of creating a new course with AI assistance"""
    if request.method == 'POST':
        form = CourseInitialPromptForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new course creation session
            session = CourseCreationSession.objects.create(
                user=request.user,
                initial_prompt=form.cleaned_data['prompt'],
                status='title_modules'
            )
            
            # Process any uploaded documents
            files = request.FILES.getlist('documents')
            if files:
                for document_file in files:
                    doc = DocumentContext.objects.create(
                        session=session,
                        document=document_file,
                    )
                    # Extract text content from the document
                    doc.content_text = extract_text_from_document(document_file)
                    doc.save()
            
            # Add the initial user message to the session
            SessionMessage.objects.create(
                session=session,
                content=form.cleaned_data['prompt'],
                is_user=True
            )
            
            # Generate initial course structure
            context_documents = session.documents.all() if session.documents.exists() else None
            ai_response = generate_course_structure(form.cleaned_data['prompt'], context_documents)
            
            if 'error' in ai_response:
                messages.error(request, ai_response['error'])
                session.delete()  # Clean up the session
                return redirect('courses:create_course_start')
            
            # Save AI response
            SessionMessage.objects.create(
                session=session,
                content=json.dumps(ai_response),
                is_user=False
            )
            
            return redirect('courses:course_creation_session', session_id=session.id)
    else:
        form = CourseInitialPromptForm()
    
    context = {
        'form': form,
    }
    return render(request, 'courses/create_course_start.html', context)

@login_required
@soc_required
def course_creation_session(request, session_id):
    """Handle the course creation session with AI"""
    session = get_object_or_404(CourseCreationSession, id=session_id, user=request.user)
    messages_list = session.messages.all().order_by('timestamp')
    
    # Get the last AI message
    try:
        last_ai_message = messages_list.filter(is_user=False).latest('timestamp')
        ai_content = last_ai_message.content
        
        # Try to parse as JSON if it is one
        try:
            ai_response = json.loads(ai_content)
            is_json = True
        except json.JSONDecodeError:
            ai_response = ai_content
            is_json = False
    except SessionMessage.DoesNotExist:
        ai_response = None
        is_json = False
    
    if request.method == 'POST':
        form = CoursePromptForm(request.POST)
        if form.is_valid():
            # Add user message
            user_prompt = form.cleaned_data['prompt']
            SessionMessage.objects.create(
                session=session,
                content=user_prompt,
                is_user=True
            )
            
            # Process based on session status
            if session.status == 'title_modules':
                # If user accepts the course structure, create the course and modules
                if "accept" in user_prompt.lower() or "create" in user_prompt.lower() or "yes" in user_prompt.lower():
                    # Create the course
                    if is_json and 'course_title' in ai_response:
                        course = Course.objects.create(
                            title=ai_response['course_title'],
                            description=ai_response.get('course_description', ''),
                            course_type=ai_response.get('course_type', 'awareness'),
                            created_by=request.user
                        )
                        
                        # Create modules
                        if 'modules' in ai_response:
                            for i, module_data in enumerate(ai_response['modules']):
                                Module.objects.create(
                                    course=course,
                                    title=module_data['title'],
                                    description=module_data.get('description', ''),
                                    order=i,
                                )
                        
                        # Update session status and link the course
                        session.course = course
                        session.status = 'chapters'
                        session.save()
                        
                        # Get the first module to define chapters
                        first_module = Module.objects.filter(course=course).order_by('order').first()
                        if first_module:
                            return redirect('courses:define_chapters', module_id=first_module.id)
                    
                    messages.error(request, "Couldn't parse the course structure properly. Please retry.")
                
                else:
                    # User wants changes, regenerate with the new prompt
                    context_documents = session.documents.all() if session.documents.exists() else None
                    new_ai_response = generate_course_structure(user_prompt, context_documents)
                    
                    if 'error' in new_ai_response:
                        messages.error(request, new_ai_response['error'])
                    else:
                        # Save new AI response
                        SessionMessage.objects.create(
                            session=session,
                            content=json.dumps(new_ai_response),
                            is_user=False
                        )
            return redirect('courses:course_creation_session', session_id=session.id)
    else:
        form = CoursePromptForm()
    
    context = {
        'session': session,
        'messages': messages_list,
        'ai_response': ai_response,
        'is_json': is_json,
        'form': form
    }
    return render(request, 'courses/course_creation_session.html', context)

@login_required
@soc_required
def define_chapters(request, module_id):
    """Define chapters for a module"""
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    
    # Verify the course belongs to the user's creation session
    try:
        session = CourseCreationSession.objects.get(course=course, user=request.user)
    except CourseCreationSession.DoesNotExist:
        messages.error(request, "You don't have permission to modify this course.")
        return redirect('courses:manage_courses')
    
    if request.method == 'POST':
        if 'generate' in request.POST:
            # Generate chapter suggestions using AI
            context_documents = session.documents.all() if session.documents.exists() else None
            ai_response = generate_chapters(
                course_title=course.title,
                module_title=module.title,
                module_description=module.description,
                context_documents=context_documents
            )
            
            if 'error' in ai_response:
                messages.error(request, ai_response['error'])
            else:
                # Save AI response
                SessionMessage.objects.create(
                    session=session,
                    content=json.dumps(ai_response),
                    is_user=False
                )
                
                # Create chapters
                if 'chapters' in ai_response:
                    # Delete existing chapters for this module first
                    Chapter.objects.filter(module=module).delete()
                    
                    # Create new chapters
                    for i, chapter_data in enumerate(ai_response['chapters']):
                        Chapter.objects.create(
                            module=module,
                            title=chapter_data['title'],
                            content='',  # Will be generated later
                            order=i,
                            is_summary=chapter_data['is_summary']
                        )
                    
                    messages.success(request, f"Created {len(ai_response['chapters'])} chapters for this module.")
        elif 'next_module' in request.POST:
            # Find the next module
            next_module = Module.objects.filter(
                course=course,
                order__gt=module.order
            ).order_by('order').first()
            
            if next_module:
                return redirect('courses:define_chapters', module_id=next_module.id)
            else:
                # No more modules, move to content generation
                session.status = 'content'
                session.save()
                
                # Get the first chapter to generate content
                first_chapter = Chapter.objects.filter(
                    module__course=course
                ).order_by('module__order', 'order').first()
                
                if first_chapter:
                    return redirect('courses:create_chapter_content', chapter_id=first_chapter.id)
                else:
                    messages.error(request, "No chapters found. Please create chapters first.")
        
        elif 'save_chapters' in request.POST:
            # Save manually entered chapters
            chapter_titles = request.POST.getlist('chapter_title')
            chapter_is_summary = request.POST.getlist('chapter_is_summary')
            
            # Delete existing chapters
            Chapter.objects.filter(module=module).delete()
            
            # Create new chapters
            for i, (title, is_summary) in enumerate(zip(chapter_titles, chapter_is_summary)):
                if title.strip():  # Only create non-empty chapters
                    Chapter.objects.create(
                        module=module,
                        title=title,
                        content='',  # Will be generated later
                        order=i,
                        is_summary=(is_summary == 'on')
                    )
            
            messages.success(request, f"Saved chapters for {module.title}")
    
    # Get existing chapters
    chapters = Chapter.objects.filter(module=module).order_by('order')
    
    # Get all modules for navigation
    all_modules = Module.objects.filter(course=course).order_by('order')
    
    context = {
        'module': module,
        'course': course,
        'chapters': chapters,
        'all_modules': all_modules,
        'session': session
    }
    return render(request, 'courses/define_chapters.html', context)

@login_required
@soc_required
def create_chapter_content(request, chapter_id):
    """Create or edit content for a chapter"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    module = chapter.module
    course = module.course
    
    # Get all chapters for navigation
    all_chapters = Chapter.objects.filter(module__course=course).order_by('module__order', 'order')
    
    # Get previous chapter - across modules if needed
    try:
        chapter_index = list(all_chapters).index(chapter)
        previous_chapter = all_chapters[chapter_index - 1] if chapter_index > 0 else None
    except (ValueError, IndexError):
        previous_chapter = None
        
    # Get next chapter - across modules if needed
    try:
        chapter_index = list(all_chapters).index(chapter)
        next_chapter = all_chapters[chapter_index + 1] if chapter_index < len(all_chapters) - 1 else None
    except (ValueError, IndexError):
        next_chapter = None
    
    # Get existing questions
    questions = Question.objects.filter(chapter=chapter).prefetch_related('choices').order_by('id')
    
    if request.method == 'POST':
        if 'generate' in request.POST:
            # AI content generation logic here
            context_documents = []
            try:
                # Get content documents from the session if available
                session = CourseCreationSession.objects.get(course=course, user=request.user)
                if session.documents.exists():
                    context_documents = session.documents.all()
            except CourseCreationSession.DoesNotExist:
                pass
            
            # Call the generate_chapter_content function from utils.py
            ai_response = generate_chapter_content(
                course_title=course.title,
                module_title=module.title,
                chapter_title=chapter.title,
                is_summary=chapter.is_summary,
                context_documents=context_documents
            )
            
            if 'error' in ai_response:
                messages.error(request, ai_response['error'])
            else:
                # Save generated content to the chapter
                chapter.content = ai_response.get('chapter_content', '')
                chapter.save()
                
                # Handle quiz questions if not a summary
                if not chapter.is_summary and 'questions' in ai_response:
                    # Delete existing questions
                    Question.objects.filter(chapter=chapter).delete()
                    
                    # Create new questions from AI response
                    for q_data in ai_response['questions']:
                        question = Question.objects.create(
                            chapter=chapter,
                            question_text=q_data['question_text']
                        )
                        
                        # Create choices for the question
                        for choice_data in q_data.get('choices', []):
                            Choice.objects.create(
                                question=question,
                                choice_text=choice_data['choice_text'],
                                is_correct=choice_data['is_correct']
                            )
                
                messages.success(request, "Content generated successfully!")
        
        elif 'save_content' in request.POST or 'next_chapter' in request.POST:
            # Save the chapter content
            chapter.content = request.POST.get('content', '')
            chapter.save()
            
            # Handle questions and choices if not a summary chapter
            if not chapter.is_summary:
                # ... question handling logic ...
                pass
            
            if 'next_chapter' in request.POST:
                if next_chapter:
                    return redirect('courses:create_chapter_content', chapter_id=next_chapter.id)
                else:
                    # All chapters are complete
                    # Update course creation session status
                    try:
                        session = CourseCreationSession.objects.get(course=course)
                        session.status = 'completed'
                        session.save()
                    except CourseCreationSession.DoesNotExist:
                        pass
                    
                    messages.success(request, f"Course '{course.title}' has been successfully created!")
                    return redirect('courses:course_detail', course_id=course.id)
    
    context = {
        'chapter': chapter,
        'module': module,
        'course': course,
        'all_chapters': all_chapters,
        'previous_chapter': previous_chapter,
        'next_chapter': next_chapter,
        'questions': questions
    }
    return render(request, 'courses/create_chapter_content.html', context)

@login_required
@soc_required
def manage_courses(request):
    """View to manage all courses created by the user"""
    courses = Course.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Get enrollment counts for each course
    for course in courses:
        course.enrollment_count = Enrollment.objects.filter(course=course).count()
    
    context = {
        'courses': courses
    }
    return render(request, 'courses/manage_courses.html', context)

@login_required
@soc_required
def edit_course(request, course_id):
    """Edit an existing course"""
    course = get_object_or_404(Course, id=course_id, created_by=request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.title}' has been updated.")
            return redirect('courses:manage_courses')
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course
    }
    return render(request, 'courses/edit_course.html', context)

@login_required
@soc_required
def define_modules(request, course_id):
    """Define or edit modules for a course"""
    course = get_object_or_404(Course, id=course_id, created_by=request.user)
    
    # Check if it's part of a creation session
    try:
        session = CourseCreationSession.objects.get(course=course, user=request.user)
    except CourseCreationSession.DoesNotExist:
        messages.error(request, "You don't have permission to modify this course.")
        return redirect('courses:manage_courses')
    
    if request.method == 'POST':
        if 'save_modules' in request.POST:
            # Get module data from the POST request
            module_titles = request.POST.getlist('module_title')
            module_descriptions = request.POST.getlist('module_description')
            module_orders = request.POST.getlist('module_order')
            
            # Delete existing modules if any
            if 'replace_existing' in request.POST:
                Module.objects.filter(course=course).delete()
            
            # Create new modules
            for title, description, order in zip(module_titles, module_descriptions, module_orders):
                if title.strip():  # Only create if title is not empty
                    try:
                        order_num = int(order)
                    except ValueError:
                        order_num = 0
                    
                    Module.objects.create(
                        course=course,
                        title=title,
                        description=description,
                        order=order_num
                    )
            
            messages.success(request, f"Modules for '{course.title}' have been saved.")
            
            # Get the first module to define chapters
            first_module = Module.objects.filter(course=course).order_by('order').first()
            if first_module:
                session.status = 'chapters'
                session.save()
                return redirect('courses:define_chapters', module_id=first_module.id)
        elif 'back' in request.POST:
            return redirect('courses:course_creation_session', session_id=session.id)
    
    # Get existing modules
    modules = Module.objects.filter(course=course).order_by('order')
    
    context = {
        'course': course,
        'modules': modules,
        'session': session
    }
    return render(request, 'courses/define_modules.html', context)

@login_required
@soc_required
def enrollment_stats(request):
    """
    View for displaying enrollment statistics and training metrics
    """
    # Get all courses
    courses = Course.objects.all()
    
    # Get overall metrics
    unique_users = Enrollment.objects.values('user').distinct().count()
    active_courses = Course.objects.filter(status='active').count() if hasattr(Course, 'status') else Course.objects.count()
    total_enrollments = Enrollment.objects.count()
    completed_enrollments = Enrollment.objects.filter(completed=True).count()
    
    # Calculate overall completion rate
    completion_rate = 0
    if total_enrollments > 0:
        completion_rate = round((completed_enrollments / total_enrollments) * 100)
    
    # Get per-course statistics with more detailed metrics
    course_stats = []
    for course in courses:
        course_enrollments = Enrollment.objects.filter(course=course)
        enrollment_count = course_enrollments.count()
        
        # Skip courses with no enrollments
        if enrollment_count == 0:
            continue
            
        completion_count = course_enrollments.filter(completed=True).count()
        
        # Calculate completion rate for this course
        completion_rate_course = round((completion_count / enrollment_count) * 100) if enrollment_count > 0 else 0
        
        # Calculate average time to completion (in days)
        avg_completion_time = "N/A"
        completed_courses = course_enrollments.filter(completed=True)
        if completed_courses.exists() and hasattr(Enrollment, 'completion_date'):
            total_days = 0
            valid_completions = 0
            
            for enrollment in completed_courses:
                if enrollment.completion_date and enrollment.enrolled_date:
                    days = (enrollment.completion_date - enrollment.enrolled_date).days
                    if days >= 0:  # Ensure valid time difference
                        total_days += days
                        valid_completions += 1
                        
            if valid_completions > 0:
                avg_completion_time = f"{total_days / valid_completions:.1f} days"
        
        # Get unique users enrolled in this course
        unique_course_users = course_enrollments.values('user').distinct().count()
        
        # Get average rating if there are any evaluations
        avg_rating = CourseEvaluation.objects.filter(
            enrollment__course=course
        ).aggregate(Avg('rating'))['rating__avg']
        
        # Calculate engagement metrics - use completed chapters in the last 30 days instead
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Check if Progress model has a 'completed_date' field for recent activity
        progress_fields = [f.name for f in Progress._meta.get_fields()]
        
        if 'completed_date' in progress_fields:
            recent_activity = Progress.objects.filter(
                enrollment__course=course,
                completed=True,
                completed_date__gte=thirty_days_ago
            ).count()
        elif 'completion_date' in progress_fields:
            recent_activity = Progress.objects.filter(
                enrollment__course=course,
                completed=True,
                completion_date__gte=thirty_days_ago
            ).count()
        else:
            # If no date field available, just count all completed progress
            recent_activity = Progress.objects.filter(
                enrollment__course=course,
                completed=True
            ).count()
        
        course_stats.append({
            'title': course.title,
            'enrollment_count': enrollment_count,
            'completion_count': completion_count,
            'completion_rate': completion_rate_course,
            'avg_rating': avg_rating,
            'unique_users': unique_course_users,
            'avg_completion_time': avg_completion_time,
            'recent_activity': recent_activity
        })
    
    # Sort courses by enrollment count (descending)
    course_stats = sorted(course_stats, key=lambda x: x['enrollment_count'], reverse=True)
    
    # Get enrollment trends (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # Check if Enrollment model has 'enrolled_date' field
    enrollment_fields = [f.name for f in Enrollment._meta.get_fields()]
    
    if 'enrolled_date' in enrollment_fields:
        enrollments_by_month = Enrollment.objects.filter(
            enrolled_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('enrolled_date')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
    else:
        # If no enrolled_date field, use created_at or fall back to simpler stats
        if hasattr(Enrollment, 'created_at'):
            enrollments_by_month = Enrollment.objects.filter(
                created_at__gte=six_months_ago
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
        else:
            # No date field available, create empty chart data
            enrollments_by_month = []
    
    # Format for chart.js
    month_labels = []
    enrollment_counts = []
    
    # If we have enrollment data by month
    if enrollments_by_month:
        # Create complete monthly range
        current_date = six_months_ago.replace(day=1)
        end_date = timezone.now().replace(day=1)
        
        months_data = {item['month'].date(): item['count'] for item in enrollments_by_month}
        
        while current_date <= end_date:
            month_labels.append(current_date.strftime("%b %Y"))
            enrollment_counts.append(months_data.get(current_date.date(), 0))
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    else:
        # Use empty data if we don't have enrollment date info
        for i in range(6):
            date = timezone.now() - timedelta(days=30*i)
            month_labels.insert(0, date.strftime("%b %Y"))
        enrollment_counts = [0] * 6
    
    # Calculate top performing departments based on completion rates
    department_stats = []
    if hasattr(User, 'non_soc_profile'):
        departments = User.objects.filter(
            non_soc_profile__isnull=False
        ).values_list('non_soc_profile__department', flat=True).distinct()
        
        for department in departments:
            if not department:  # Skip null departments
                continue
                
            # Get users in this department
            department_users = User.objects.filter(non_soc_profile__department=department)
            if not department_users.exists():
                continue
                
            # Calculate department metrics
            dept_enrollments = Enrollment.objects.filter(user__in=department_users)
            dept_completed = dept_enrollments.filter(completed=True).count()
            dept_total = dept_enrollments.count()
            
            if dept_total > 0:
                completion_rate_dept = round((dept_completed / dept_total) * 100)
                department_stats.append({
                    'name': department,
                    'user_count': department_users.count(),
                    'completion_rate': completion_rate_dept,
                    'enrollments': dept_total,
                    'completions': dept_completed
                })
        
        # Sort departments by completion rate
        department_stats = sorted(department_stats, key=lambda x: x['completion_rate'], reverse=True)
    
    context = {
        'unique_users': unique_users,
        'total_enrollments': total_enrollments,
        'courses_completed': completed_enrollments,
        'active_courses': active_courses,
        'completion_rate': completion_rate,
        'course_stats': course_stats,
        'month_labels': json.dumps(month_labels),
        'enrollment_counts': json.dumps(enrollment_counts),
        'department_stats': department_stats,
        'title': 'Training Metrics and Enrollment Statistics'
    }
    
    return render(request, 'courses/enrollment_stats.html', context)

@login_required
def course_complete(request, course_id):
    """Mark a course as completed"""
    course = get_object_or_404(Course, pk=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You need to enroll in this course first.")
        return redirect('courses:course_detail', course_id=course.id)
    
    # Mark as completed
    enrollment.completed = True
    enrollment.completion_date = timezone.now()
    enrollment.save()
    
    messages.success(request, f"Congratulations! You've completed the course '{course.title}'.")
    
    # Check if there's an associated awareness module and redirect if so
    try:
        awareness_module = course.awareness_module
        if awareness_module:
            messages.info(request, f"Take the awareness module to test your knowledge and earn points!")
            return redirect('awareness:take_module', module_id=awareness_module.id)
    except:
        pass
    
    return redirect('courses:course_detail', course_id=course.id)