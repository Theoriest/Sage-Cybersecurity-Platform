# Sage Cybersecurity Training Platform Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [User Types and Roles](#user-types-and-roles)
4. [Core Modules](#core-modules)
   - [Courses Module](#courses-module)
   - [Awareness Module](#awareness-module)
   - [SOC Module](#soc-module)
   - [Non-SOC Module](#non-soc-module)
5. [Key Features](#key-features)
   - [AI-Driven Course Creation](#ai-driven-course-creation)
   - [Learning Management](#learning-management)
   - [Awareness Assessment](#awareness-assessment)
   - [Security Operation Center Tools](#security-operation-center-tools)
   - [Progress Tracking](#progress-tracking)
6. [Technical Implementation](#technical-implementation)
   - [Backend Framework](#backend-framework)
   - [Database Schema](#database-schema)
   - [AI Integration](#ai-integration)
   - [File Processing](#file-processing)
7. [API Documentation](#api-documentation)
8. [Development and Deployment](#development-and-deployment)
9. [Future Enhancements](#future-enhancements)
10. [Troubleshooting](#troubleshooting)
11. [Codebase Structure and Templates](#codebase-structure-and-templates)

## Introduction

The Sage Cybersecurity Training Platform is a comprehensive learning management system designed to deliver cybersecurity training, awareness modules, and practical tools for both security professionals (SOC) and non-technical staff (Non-SOC). The platform leverages artificial intelligence to generate personalized learning content, assessments, and analytics.

The primary goal of Sage is to improve an organization's security posture by ensuring all employees have appropriate levels of cybersecurity knowledge and awareness. The platform achieves this through structured courses, assessment modules, and real-world security operation center functionalities.

## System Architecture

Sage is built on a modular architecture using the Django web framework. The system consists of four primary modules:

1. **Courses**: Manages course creation, content generation, learning materials, and student enrollment
2. **Awareness**: Handles security awareness assessments, quizzes, and certification
3. **SOC**: Provides specialized tools for security professionals
4. **Non-SOC**: Delivers appropriate content and experiences for general staff

The platform utilizes AI services via HuggingFace's inference API to dynamically generate course content, questions, and adaptive learning paths. Data is stored in a relational database with models designed to track detailed user progress and performance metrics.

## User Types and Roles

Sage supports multiple user roles to accommodate different needs within an organization:

1. **SOC Users**: Security professionals who can:
   - Create and manage courses
   - Design awareness modules
   - Access security metrics and analytics
   - Manage incidents and security reports
   - Create playbooks and task assignments

2. **Non-SOC Users**: General staff who can:
   - Enroll in courses
   - Take awareness assessments
   - Track their security awareness level
   - Submit security questions and requests
   - Earn certificates and achievements

3. **Administrators**: System administrators who can:
   - Manage all users and content
   - Configure system settings
   - Access all analytics and reports

## Core Modules

### Courses Module

The Courses module is the foundation of the training platform, enabling the creation and delivery of structured cybersecurity learning content.

**Key Components:**
- Course creation workflow with AI assistance
- Module and chapter organization
- Content generation from prompts and uploaded reference documents
- Quiz generation and assessment
- Enrollment management
- Progress tracking
- Course analytics

**Key Models:**
- `Course`: Represents a complete training course
- `Module`: Divides courses into logical sections
- `Chapter`: Individual learning units with content and quizzes
- `Question`/`Choice`: Quiz components for learning assessment
- `Enrollment`: Tracks user registration in courses
- `Progress`: Records user advancement through chapters
- `CourseEvaluation`: Captures user feedback
- `CourseCreationSession`: Manages the AI-assisted course creation process

### Awareness Module

The Awareness module provides a mechanism to assess and verify user understanding of cybersecurity concepts through focused testing modules.

**Key Components:**
- Assessment module creation
- Question management (manual and AI-generated)
- Module difficulty and point systems
- Test administration
- Result review and analytics
- User performance tracking

**Key Models:**
- `AwarenessModule`: Defines assessment parameters
- `Question`: Assessment questions with various formats
- `Answer`: Response options for questions
- `ModuleAttempt`: Records user test attempts
- `UserResponse`: Captures individual answers

### SOC Module

The SOC module provides specialized tools for security professionals to manage security operations.

**Key Components:**
- Security incident management
- Alert processing
- Playbook templates
- Task assignment and tracking
- Security metrics dashboards
- Report generation

**Key Models:**
- `SecurityIncident`: Tracks security events
- `Alert`: Manages system notifications
- `SocTask`: Handles task assignment and workflow
- `PlaybookTemplate`: Standardizes response procedures
- `SecurityReport`: Documents security findings
- `SecurityMetric`: Tracks key performance indicators

### Non-SOC Module

The Non-SOC module delivers appropriate cybersecurity training and resources for general staff.

**Key Components:**
- Personalized learning dashboard
- Progress visualization
- Achievement tracking
- Security request submission
- Article access
- Awareness level progression

**Key Models:**
- User progress tracking
- Security request management
- Notification handling
- Achievement records

## Key Features

### AI-Driven Course Creation

The platform leverages state-of-the-art AI models to streamline the course creation process:

**Workflow:**
1. Instructors provide initial course topic, goals, and optional reference materials
2. AI generates course structure (title, description, modules)
3. AI creates detailed chapters for each module
4. AI generates comprehensive content for each chapter
5. AI produces quiz questions to assess understanding
6. Instructors can review and edit all generated content

**Implementation Details:**
- Primary AI provider: Together AI using DeepSeek-R1 model
- Fallback AI provider: HuggingFace Inference API using Qwen2-72B-Instruct
- Context enhancement using uploaded documents (PDF, DOCX, TXT, PPT, PPTX)
- JSON parsing for structured data extraction
- Error handling and fallback mechanisms

### Learning Management

Sage provides comprehensive learning management capabilities:

- Course enrollment and progress tracking
- Chapter-by-chapter learning paths
- Interactive quizzes with immediate feedback
- Bookmarking and resumption of learning sessions
- Course completion certificates
- Learning analytics and reporting

### Awareness Assessment

The platform includes a robust system for testing and verifying security awareness:

- Configurable assessment modules with difficulty levels
- Multiple question types (single-choice, multiple-choice)
- Timed assessments with performance metrics
- Question rotation for repeated attempts
- Detailed feedback and result review
- Point-based rewards for successful completion

### Security Operation Center Tools

For security professionals, Sage provides practical SOC tools:

- Incident tracking and management
- Alert management with priority levels
- Task assignment and tracking
- Playbook creation and management
- Metrics visualization and reporting
- Team coordination features

### Progress Tracking

Comprehensive progress tracking features include:

- Visual progress indicators
- Completion percentages
- Awareness level progression (Levels 1-5)
- Security awareness badges and achievements
- Performance analytics and improvement suggestions
- Certification tracking

## Technical Implementation

### Backend Framework

Sage is built using the Django web framework, taking advantage of its:

- Model-View-Template (MVT) architecture
- Authentication and authorization system
- Admin interface for content management
- ORM for database operations
- Form handling and validation
- Security features (CSRF protection, XSS prevention)

### Database Schema

The database schema is organized around the core modules and their relationships:

- User-related models (extending Django's User model)
- Course-related models (Course, Module, Chapter, etc.)
- Awareness-related models (AwarenessModule, Question, etc.)
- SOC-related models (Incident, Alert, Task, etc.)
- Non-SOC models (requests, achievements, etc.)

The schema enforces data integrity through:
- Foreign key relationships
- Unique constraints
- Cascading deletes where appropriate
- Soft deletion for critical data

### AI Integration

AI capabilities are integrated through HuggingFace's Inference API:

- Client initialization with API key
- Model selection based on task requirements
- Primary/fallback model strategy
- Prompt engineering for optimal results
- Response parsing and validation
- Error handling and logging

**Key AI Function Flow:**
1. Prepare system prompt and user context
2. Send to primary AI model (Together AI/DeepSeek-R1)
3. If failed, fall back to secondary model (HuggingFace/Qwen2)
4. Parse and validate structured response
5. Apply data corrections if needed
6. Return formatted results

### File Processing

The platform supports document processing for context enhancement:

**Supported Formats:**
- PDF (using PyPDF2)
- DOCX (using python-docx)
- TXT (plain text)
- PPT/PPTX (using python-pptx, when available)

**Processing Flow:**
1. File upload and validation
2. Content extraction based on format
3. Text processing and normalization
4. Integration with AI context
5. Error handling for corrupted files

## API Documentation

Sage primarily uses internal API endpoints for frontend-backend communication:

### Courses Module Endpoints

- `/courses/api/course-create/`: Creates a new course
- `/courses/api/module-create/`: Creates modules within a course
- `/courses/api/chapter-content/`: Generates/retrieves chapter content
- More endpoints detailed in separate API documentation

### Awareness Module Endpoints

- `/awareness/api/question-generate/`: Generates assessment questions
- `/awareness/api/attempt-start/`: Initializes an assessment attempt
- `/awareness/api/submit-response/`: Records user responses
- Additional endpoints detailed in separate API documentation

## Development and Deployment

### Development Setup

1. Clone the repository: `git clone https://github.com/your-org/sage.git`
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Apply migrations: `python manage.py migrate`
5. Create superuser: `python manage.py createsuperuser`
6. Run development server: `python manage.py runserver`

### Environment Variables

Configure the following environment variables:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to 'True' for development, 'False' for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_URL`: Database connection string
- `HUGGINGFACE_API_KEY`: API key for HuggingFace
- Additional configuration variables as needed

### Deployment Considerations

For production deployment:
1. Use a production-ready database (PostgreSQL recommended)
2. Configure a web server (Nginx, Apache)
3. Use WSGI server (Gunicorn, uWSGI)
4. Set up SSL/TLS certificates
5. Implement proper backup procedures
6. Configure caching for improved performance

## Future Enhancements

Planned enhancements for future releases:

1. **Mobile Application**: Native mobile apps for iOS and Android
2. **Advanced Analytics**: Enhanced reporting and predictive analytics
3. **Gamification**: Expanded achievement system and competitive elements
4. **Enhanced AI**: More personalized learning recommendations
5. **API Expansion**: Public API for third-party integrations
6. **Offline Mode**: Support for offline learning and synchronization

## Troubleshooting

### Common Issues and Solutions

**AI Content Generation Failures:**
- Check API key validity and quota limits
- Verify network connectivity to AI providers
- Review logs for specific error messages
- Test with smaller prompts to isolate issues

**File Processing Errors:**
- Ensure proper file format and encoding
- Check for file corruption or password protection
- Verify library dependencies are installed correctly

**Database Performance:**
- Add appropriate indexes to frequently queried fields
- Optimize complex queries
- Consider database caching strategies
- Review database connection pool settings

**General Performance:**
- Implement template fragment caching
- Use pagination for large data sets
- Optimize static file delivery
- Consider CDN for static assets

For additional support, consult the developer community forums or submit issues through the project's issue tracking system.

## Codebase Structure and Templates

### Directory Organization

The Sage codebase follows a modular structure organized around Django apps:

```
/home/lee/Documents/Sage/
├── docs/                     # Documentation files
├── requirements.txt          # Python dependencies
├── src/
│   └── Cybersec/            # Main Django project
│       ├── Awareness/        # Security awareness assessment module
│       ├── Articles/         # Security articles management
│       ├── Courses/          # Course management and learning
│       ├── Cybersec/         # Project settings and core files
│       ├── NonSoc/           # Non-SOC user interfaces
│       ├── Soc/              # Security Operations Center tools
│       └── user/             # User management and authentication
```

### Key Templates

The system includes a variety of template files for different functionalities:

#### SOC Module Templates

1. **Dashboard**
   - `soc/dashboard.html`: Main SOC user dashboard with metrics and quick actions
   - `soc/metrics_dashboard.html`: Detailed security metrics visualization

2. **Incident Management**
   - `soc/incident_list.html`: List view of security incidents
   - `soc/incident_detail.html`: Detailed view of security incident
   - `soc/incident_form.html`: Creation/editing form for incidents
   - `soc/create_incident.html`: Simplified incident creation form

3. **Alert Management**
   - `soc/alert_list.html`: List view of security alerts
   - `soc/alert_detail.html`: Detailed view of security alert
   - `soc/alert_form.html`: Creation/editing form for alerts

4. **Task Management**
   - `soc/task_list.html`: List view of SOC tasks
   - `soc/task_detail.html`: Detailed view of task
   - `soc/task_form.html`: Creation/editing form for tasks

5. **Report Management**
   - `soc/report_list.html`: List view of security reports
   - `soc/report_detail.html`: Detailed view of security report
   - `soc/report_form.html`: Creation/editing form for reports

6. **Playbook Management**
   - `soc/playbook_list.html`: List view of incident response playbooks
   - `soc/playbook_detail.html`: Detailed view of playbook
   - `soc/playbook_form.html`: Creation/editing form for playbooks

7. **Security Request Management**
   - `soc/security_request_list.html`: List view of security requests
   - `soc/security_request_detail.html`: Detailed view of security request

#### Non-SOC Module Templates

1. **Dashboard**
   - `NonSoc/nonsoc_dashboard.html`: Main dashboard for non-technical users

2. **Security Awareness**
   - `NonSoc/user_progress.html`: User's learning progress and achievements
   - `NonSoc/notifications.html`: User notification center

3. **Security Requests**
   - `NonSoc/create_security_request.html`: Form to submit security questions
   - `NonSoc/security_request_detail.html`: View security request details

4. **Articles**
   - `NonSoc/article_list.html`: List of security awareness articles
   - `NonSoc/article_detail.html`: Detailed view of article

#### Awareness Module Templates

1. **Modules**
   - `Awareness/module_list.html`: List of awareness assessment modules
   - `Awareness/module_detail.html`: Module overview and management
   - `Awareness/module_detail_analytics.html`: Performance analytics

2. **Assessments**
   - `Awareness/complete_module.html`: Interface for taking assessments
   - `Awareness/manage_questions.html`: Question management interface

3. **Question Management**
   - `Awareness/add_question.html`: Form for adding assessment questions

#### Courses Module Templates

1. **Course Management**
   - `courses/course_list.html`: List of available courses
   - `courses/course_detail.html`: Course overview and management

2. **Learning Interface**
   - `courses/course_learn.html`: Main learning interface
   - `courses/chapter_view.html`: Chapter content and quiz

3. **Course Creation**
   - `courses/create_course_start.html`: Initial course creation
   - `courses/create_course_details.html`: Course details form
   - `courses/create_course_modules.html`: Module creation interface

### Template Design Patterns

The Sage platform implements several consistent design patterns across templates:

1. **Base Templates**
   - `base.html`: Core template with common structure
   - `base_nonsoc.html`: Base template for non-SOC interface

2. **Navigation Elements**
   - Breadcrumbs for hierarchical navigation
   - Context-aware sidebars
   - Responsive navigation bars

3. **Card-Based Components**
   - Consistent use of cards for content organization
   - Standardized headers, footers, and actions

4. **Data Visualization**
   - Progress indicators
   - Charts and graphs
   - Severity and status indicators

5. **Interactive Elements**
   - Form validation and error handling
   - AJAX-powered dynamic content
   - Filtering and sorting interfaces

6. **Responsive Design**
   - Mobile-friendly layouts
   - Adaptive content presentation
   - Consistent behavior across device sizes

This structured approach to templates ensures a cohesive user experience while maintaining clear separation between different functional areas of the platform.
