# utils/ai_helper.py

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import google.generativeai as genai

load_dotenv()

# Correctly load API key from .env
genai.configure(api_key=os.getenv("AIzaSyBVItFfnn88M1SzisfHo_nkMvW31ZBL2mg"))

# Replace 'gemini-pro' with a valid model from your API key
model = genai.GenerativeModel('gemini-1')  # <-- use a valid model, check with list_models()

def get_ai_response(prompt):
    """Get AI response from Google Gemini API"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if hasattr(response, 'text') else str(response)
    except Exception as e:
        return f"AI service temporarily unavailable. Please try again later. Error: {str(e)}"

def suggest_appointment_time(doctor_schedule, existing_appointments):
    """Suggest best appointment time using AI"""
    prompt = f"""
    Based on the doctor's available times: {doctor_schedule}
    And existing appointments: {existing_appointments}
    
    Suggest the 3 best time slots for a new appointment today or tomorrow.
    Avoid busy hours. Return times in HH:MM (24-hour).
    """
    return get_ai_response(prompt)

def get_health_advice(symptoms):
    """Get health advice based on symptoms"""
    prompt = f"""
    Patient symptoms: {symptoms}
    
    Provide brief, general health advice (not a diagnosis).
    Include:
    1. Possible common causes
    2. Self-care tips
    3. When to see a doctor
    
    Keep it under 200 words and emphasize this is not medical diagnosis.
    """
    return get_ai_response(prompt)

def generate_health_tips(category='general'):
    """Generate daily health tips"""
    prompt = f"""
    Generate a helpful health tip about {category}.
    Make it practical, actionable, under 100 words.
    """
    return get_ai_response(prompt)

def analyze_appointment_patterns(appointments_data):
    """Analyze appointment patterns for admin insights"""
    prompt = f"""
    Analyze these appointment statistics: {appointments_data}
    
    Provide insights on:
    1. Busiest times/days
    2. Most requested specializations
    3. Appointment completion rate
    4. Recommendations for scheduling optimization
    
    Keep it concise and actionable.
    """
    return get_ai_response(prompt)
