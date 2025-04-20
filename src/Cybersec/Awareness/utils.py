import json
import logging
from django.conf import settings
from Courses.utils import get_hf_inference_client, get_hf_fallback_client

logger = logging.getLogger(__name__)

def generate_awareness_questions(module, additional_context=None):
    """
    Generate questions for an awareness module based on its associated course
    
    Args:
        module: AwarenessModule instance
        additional_context: Optional string with additional context for generation
    
    Returns:
        dict: A dictionary containing generated questions or error information
    """
    logger.info(f"Generating questions for awareness module: {module.title}")
    
    client = get_hf_inference_client()
    fallback_client = get_hf_fallback_client()
    
    # Get course information
    course = module.course
    course_modules = course.modules.all().order_by('order')
    
    # Build context from course modules information
    context = f"Course Title: {course.title}\nCourse Description: {course.description}\n\n"
    context += "Course Modules:\n"
    
    for i, course_module in enumerate(course_modules):
        context += f"Module {i+1}: {course_module.title} - {course_module.description}\n"
    
    # Add additional context if provided
    if additional_context:
        context += f"\nAdditional Context:\n{additional_context}\n"
        
    # Create system prompt for generating questions
    system_prompt = f"""You are an expert in creating assessment questions for cybersecurity awareness training.
    
    Generate a set of questions for the awareness module "{module.title}" with difficulty level "{module.get_difficulty_display()}".
    
    Create exactly 2 questions for each course module - one single choice question and one multiple choice question.
    These questions should test understanding of key concepts in each module.
    
    Respond in JSON format with this structure:
    {{
        "questions": [
            {{
                "module_number": 0,  // 0-based index of the course module
                "text": "Question text",
                "question_type": "single",  // "single" or "multiple"
                "explanation": "Detailed explanation of the answer that will be shown during review",
                "answers": [
                    {{"text": "Answer 1", "is_correct": true, "explanation": "Why this answer is correct/incorrect"}},
                    {{"text": "Answer 2", "is_correct": false, "explanation": "Why this answer is correct/incorrect"}},
                    {{"text": "Answer 3", "is_correct": false, "explanation": "Why this answer is correct/incorrect"}},
                    {{"text": "Answer 4", "is_correct": false, "explanation": "Why this answer is correct/incorrect"}}
                ]
            }},
            // More questions follow...
        ]
    }}
    
    For single-choice questions, ensure exactly ONE answer is marked as correct.
    For multiple-choice questions, mark TWO OR MORE answers as correct.
    
    Make sure questions:
    1. Are realistic and challenging, appropriate for the {module.get_difficulty_display()} difficulty level
    2. Have clear, unambiguous answers
    3. Test understanding of course material thoroughly
    4. Include detailed explanations for all answers
    """
    
    try:
        logger.info("Sending request to primary HF model (DeepSeek-R1)")
        
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            max_tokens=3000
        )
        response_text = completion.choices[0].message.content
        logger.info(f"Received response from primary model, length: {len(response_text)} characters")
        
    except Exception as e:
        logger.warning(f"Primary model failed, using fallback: {e}")
        
        try:
            logger.info("Sending request to fallback HF model (Qwen)")
            
            completion = fallback_client.chat.completions.create(
                model="Qwen/Qwen2-72B-Instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=3000
            )
            response_text = completion.choices[0].message.content
            logger.info(f"Received response from fallback model, length: {len(response_text)} characters")
            
        except Exception as e2:
            logger.error(f"Both models failed: {e2}")
            return {"error": "Failed to generate questions due to API issues."}
    
    # Try to extract JSON from the response
    try:
        # First attempt - direct parsing
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Second attempt - search for JSON in the text
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                result = json.loads(json_text)
            else:
                raise ValueError("No valid JSON found in the response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            return {"error": "Failed to parse the generated questions."}
    
    return result

def validate_generated_questions(data):
    """
    Validate the generated questions data structure
    
    Args:
        data: The JSON data returned from the API
        
    Returns:
        tuple: (is_valid, errors)
    """
    if "error" in data:
        return False, [data["error"]]
        
    errors = []
    
    if "questions" not in data:
        return False, ["No questions found in the generated data"]
        
    questions = data["questions"]
    if not isinstance(questions, list) or len(questions) == 0:
        return False, ["Questions must be a non-empty list"]
        
    # Validate each question
    for i, question in enumerate(questions):
        if "text" not in question:
            errors.append(f"Question {i+1} is missing text")
            
        if "question_type" not in question:
            errors.append(f"Question {i+1} is missing question_type")
        elif question["question_type"] not in ["single", "multiple"]:
            errors.append(f"Question {i+1} has invalid question_type: {question['question_type']}")
            
        if "module_number" not in question:
            errors.append(f"Question {i+1} is missing module_number")
            
        if "answers" not in question or not isinstance(question["answers"], list):
            errors.append(f"Question {i+1} has no valid answers list")
            continue
            
        # Check for correct answers
        correct_answers = sum(1 for answer in question["answers"] if answer.get("is_correct"))
        
        if question.get("question_type") == "single" and correct_answers != 1:
            errors.append(f"Single-choice question {i+1} must have exactly 1 correct answer, found {correct_answers}")
            
        if question.get("question_type") == "multiple" and correct_answers < 2:
            errors.append(f"Multiple-choice question {i+1} must have at least 2 correct answers, found {correct_answers}")
    
    return len(errors) == 0, errors
