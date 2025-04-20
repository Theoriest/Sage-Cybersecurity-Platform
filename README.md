# Sage Cybersecurity Training Platform

A comprehensive learning management system for cybersecurity training, featuring AI-driven course creation, awareness assessments, and specialized tools for security professionals.

## Overview

Sage is designed to improve an organization's security posture by ensuring all employees have appropriate levels of cybersecurity knowledge and awareness. The platform delivers structured courses, assessment modules, and practical security operation center functionalities.

## Key Features

- **AI-Driven Course Creation**: Generate comprehensive cybersecurity courses using state-of-the-art AI models
- **Learning Management**: Course enrollment, progress tracking, and certification
- **Awareness Assessment**: Configurable security awareness modules with diverse question types
- **Security Operation Center Tools**: Incident management, alert processing, and security metrics
- **Progress Tracking**: Visual indicators and awareness level progression

## System Requirements

- Python 3.8+
- Django 3.2+
- PostgreSQL (recommended for production)
- HuggingFace API access

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure environment variables in `.env` file
6. Apply migrations: `python manage.py migrate`
7. Create superuser: `python manage.py createsuperuser`
8. Run development server: `python manage.py runserver`

## Environment Variables and Settings

For security reasons, sensitive settings are not included in the repository. Follow these steps to set up your environment:

1. Copy the settings template to create your local settings:
   ```
   cp src/Cybersec/Cybersec/settings_template.py src/Cybersec/Cybersec/settings.py
   ```

2. Create a `.env` file in the project root with your secret values:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file and add your actual secrets:
   ```
   DJANGO_SECRET_KEY=your_django_secret_key_here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgresql://user:password@localhost/dbname
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   ```

The application will load these environment variables automatically when it starts.

## Documentation

More detailed documentation can be found in the [docs directory](/docs/project_documentation.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting Git Issues

If you encounter Git push errors like "non-fast-forward", follow these steps:

1. First, fetch the latest changes from the remote:
   ```
   git fetch origin
   ```

2. If you want to keep both your changes and the remote changes, use:
   ```
   git pull --rebase origin main
   ```

3. If you encounter conflicts during rebase, resolve them and then:
   ```
   git add .
   git rebase --continue
   ```

4. After successfully rebasing, push to GitHub with:
   ```
   git push origin main
   ```

5. If you want to force push (only if you're sure about overwriting remote changes):
   ```
   git push -f origin main
   ```
   Note: Use force push with caution as it can overwrite others' work.
