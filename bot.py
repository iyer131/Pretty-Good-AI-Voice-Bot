from flask import Flask, request
from dotenv import load_dotenv
import os
from signalwire.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from openai import OpenAI
from datetime import datetime

app = Flask(__name__)
load_dotenv('prettyGood.env')

project_id = os.environ['SIGNALWIRE_PROJECT_ID']
auth_token = os.environ['SIGNALWIRE_AUTH_TOKEN']
space_url = os.environ['SIGNALWIRE_SPACE_URL']
open_ai_key = os.environ['OPENAI_API_KEY']

client = Client(project_id, auth_token, signalwire_space_url=space_url)
openAIClient = OpenAI(api_key=open_ai_key)
transcript_files = [
    'transcript_schedule.txt', 'transcript_reschedule.txt', 'transcript_cancel.txt',
    'transcript_refill.txt', 'transcript_location.txt', 'transcript_insurance.txt',
    'transcript_weekend.txt', 'transcript_midnight.txt', 'transcript_wrong_number.txt',
    'transcript_emergency.txt', 'transcript_angry.txt',
    'bugs_schedule.txt', 'bugs_reschedule.txt', 'bugs_cancel.txt',
    'bugs_refill.txt', 'bugs_location.txt', 'bugs_insurance.txt',
    'bugs_weekend.txt', 'bugs_midnight.txt', 'bugs_wrong_number.txt',
    'bugs_emergency.txt', 'bugs_angry.txt'
]
@app.route('/call', methods = ['GET'])
def call():
    
    scenario_files = {
    'schedule_appointment': ('transcript_schedule.txt', 'bugs_schedule.txt'),
    'reschedule_appointment': ('transcript_reschedule.txt', 'bugs_reschedule.txt'),
    'cancel_appointment': ('transcript_cancel.txt', 'bugs_cancel.txt'),
    'medication_refill': ('transcript_refill.txt', 'bugs_refill.txt'),
    'location_questions': ('transcript_location.txt', 'bugs_location.txt'),
    'insurance_questions': ('transcript_insurance.txt', 'bugs_insurance.txt'),
    'weekend_appointment': ('transcript_weekend.txt', 'bugs_weekend.txt'),
    'midnight_appointment': ('transcript_midnight.txt', 'bugs_midnight.txt'),
    'wrong_number': ('transcript_wrong_number.txt', 'bugs_wrong_number.txt'),
    'emergency': ('transcript_emergency.txt', 'bugs_emergency.txt'),
    'angry_patient': ('transcript_angry.txt', 'bugs_angry.txt')
}

    scenario = request.args.get('scenario')

    if scenario in scenario_files:
        for f in scenario_files[scenario]:
            open(f, 'w').close()
    
    contexts = {
        'schedule_appointment': context_appt,
        'reschedule_appointment': context_reschedule,
        'cancel_appointment': context_cancel,
        'medication_refill': context_refill,
        'location_questions': context_location,
        'insurance_questions': context_insurance,
        'weekend_appointment': context_weekend,
        'midnight_appointment': context_midnight,
        'wrong_number': context_wrong_person,
        'emergency': context_emergency,
        'angry_patient': context_angry
    }

    if scenario in contexts:
        context= contexts[scenario]
        message = context[0]
        context.clear()
        context.append(message)
    
    call = client.calls.create(
        url=f"https://inculcative-ceremonially-leonidas.ngrok-free.dev/{scenario}",
        to=os.environ['TARGET_PHONE_NUMBER'],
        from_=os.environ['SIGNALWIRE_PHONE_NUMBER']
    )
    print(call.sid)
    return "Call started"

context_bugs = [{"role": "system", "content": 
    "You are a QA engineer reviewing a conversation transcript between a patient bot and a medical AI agent. "
    "You are evaluating the AGENT's behavior only — not the patient bot. "
    "Only flag bugs that would have a real negative impact on a patient's experience or healthcare outcome. "
    "Do NOT flag minor issues like spelling variations, speech-to-text transcription artifacts, or stylistic choices. "
    "Do NOT flag bugs where the agent explicitly says it is in demo or test mode — these are expected. "
    "Do NOT flag issues caused by the patient bot. "
    "Do NOT make assumptions about dates, times, or context not present in the transcript. Only flag issues clearly visible in the transcript. "
    "Focus on HIGH IMPACT bugs such as: incorrect appointment details, failure to handle emergencies properly, "
    "giving wrong medical information, scheduling at impossible times, or failing to complete a reasonable patient request. "
    "Do NOT flag it as a bug if the agent refuses to cancel an appointment that has already passed — this is correct behavior."
    "The agent has access to the current date and time and its statements about whether appointments are in the past or future should be trusted as accurate."
    "Do NOT flag issues about the agent not being able to find your patient records, since this is a demo and test."
    "For each bug found, include: "
    "1. A short description of the bug. "
    "2. Severity (Low, Medium, High). "
    "3. The transcript file where the bug was found (you will be told the filename). "
    "4. The exact quote from the transcript where the bug occurs. "
    "5. Why it is a problem and what the agent should have done instead. "
    "Keep the format consistent across all bugs. "
    "Note: the current date and time is " + datetime.now().strftime("%A, %B %d, %Y at %I:%M %p") + ". Use this to evaluate whether any time-related agent responses are correct."
    "If no bugs are found, say 'No bugs found.'"}]
def find_bugs(transcript, fileName, context):
     fresh_context = [context[0]]  
     fresh_context.append({"role": "user", "content": f"Transcript file: {fileName}\n{transcript}"})
     response = openAIClient.chat.completions.create(
              model="gpt-4o-mini",
              messages=fresh_context 
        )
     bugs_file = fileName.replace("transcript_", "bugs_")
     with open(bugs_file, "a", encoding="utf-8") as f:
            f.write(response.choices[0].message.content)

def process(fileName, routeName, context):
    transcribe = request.form.get('SpeechResult') 
    # Gather is for listening to the agent first 
    if not transcribe:
        response = VoiceResponse()
        gather = Gather(input='speech', action=routeName, method="POST", timeout=10, speechTimeout=4, language='en-US', enhanced='true')
        response.append(gather)
        return str(response)
       
    else: 
        context.append({"role": 'user', "content": transcribe})
        speak = openAIClient.chat.completions.create(
              model="gpt-4o-mini",
              messages=context 
        )
        with open(fileName, "a", encoding="utf-8") as f:
            f.write(f"Agent: {transcribe}\n")
            f.write(f"Bot: {speak.choices[0].message.content}\n")
        if "BYE" in speak.choices[0].message.content:
            clean_response = speak.choices[0].message.content
            with open(fileName, "r", encoding="utf-8") as f:
                transcript = f.read()
            find_bugs(transcript, fileName, context_bugs)
            response = VoiceResponse()
            response.say(clean_response)
            response.hangup()
            return str(response)
        context.append({"role": "assistant", "content": speak.choices[0].message.content})

    response = VoiceResponse()
    gather = Gather(input='speech', action=routeName, method="POST", timeout = 10, speechTimeout=4, language='en-US', enhanced='true')
    gather.say(speak.choices[0].message.content)
    response.append(gather)
    return str(response)


context_appt = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to schedule an appointment. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "You have a specific reason for your visit such as a routine checkup, back pain, knee pain, etc. "
    "When the agent asks you questions, answer them as a real patient would — give your name, date of birth, insurance, preferred times, etc. "
    "Never ask the agent what type of appointment they need — YOU are the one who needs the appointment. "
    "When the appointment is successfully scheduled, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/schedule_appointment', methods = ['POST'])
def schedule_appt():
    return process("transcript_schedule.txt", "/schedule_appointment", context_appt)


context_reschedule = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to reschedule an existing appointment."
    "You are NOT the receptionist or agent. You are the one calling in. "
    "You have an existing appointment next week that you need to move to a different date and time. "
    "When the agent asks you questions, answer them as a real patient would — give your name, date of birth, current appointment details, preferred new times, etc. "
    "When the appointment is successfully rescheduled, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/reschedule_appointment', methods=['POST'])
def reschedule_appt():
    return process("transcript_reschedule.txt", "/reschedule_appointment", context_reschedule)


context_cancel = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to cancel an existing appointment."
    "You are NOT the receptionist or agent. You are the one calling in. "
    "You want to cancel your upcoming appointment and do not want to reschedule. "
    "When the agent asks you questions, answer them as a real patient would — give your name, date of birth, and appointment details. "
    "When the appointment is successfully canceled, end your final response with the word BYE."
    "Do not invent appointment details. Only refer to appointments that the agent explicitly mentions. "
    "If the agent lists your upcoming appointments, choose one from that list to cancel. "
    "Do not make up dates or times that were not mentioned by the agent."
    "If the agent says an appointment is already in the past, acknowledge it and ask the agent to list your other upcoming appointments so you can choose one to cancel instead."
    "Your birth date is March 15th, 1985."}]
@app.route('/cancel_appointment', methods=['POST'])
def cancel_appt():
    return process("transcript_cancel.txt", "/cancel_appointment", context_cancel)


context_refill = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to request a medication refill. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "You need a refill for a realistic medication such as lisinopril, metformin, or atorvastatin. "
    "When the agent asks you questions, answer them as a real patient would — give your name, date of birth, pharmacy details, and medication name. "
    "When the refill is successfully requested, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/medication_refill', methods=['POST'])
def medication_refill():
    return process("transcript_refill.txt", "/medication_refill", context_refill)


context_location = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to ask about their location and directions. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "Ask about the office address, nearby landmarks, parking availability, and public transit options. "
    "When your questions are answered, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/location_questions', methods=['POST'])
def location_questions():
    return process("transcript_location.txt", "/location_questions", context_location)


context_insurance = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to ask about accepted insurance plans. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "Ask whether the office accepts your specific insurance plan (Blue Cross Blue Shield), whether they are in-network, "
    "what the copay might be, and whether they accept Medicare or Medicaid. "
    "When your questions are answered, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/insurance_questions', methods=['POST'])
def insurance_questions():
    return process("transcript_insurance.txt", "/insurance_questions", context_insurance)


context_weekend = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to schedule an appointment on a weekend. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "Insist that you can only come in on Saturday or Sunday. If the agent says they are closed, push back and ask if any exception can be made. "
    "Be persistent but polite. "
    "When the conversation reaches a natural end, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/weekend_appointment', methods=['POST'])
def weekend_appt():
    return process("transcript_weekend.txt", "/weekend_appointment", context_weekend)


context_midnight = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office to schedule an appointment at an unusual time. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "Request an appointment at midnight or 3 AM, claiming those are the only times you are available. "
    "If the agent says they are closed at that time, insist and ask if any doctor is available after hours. "
    "When the conversation reaches a natural end, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/midnight_appointment', methods=['POST'])
def midnight_appt():
    return process("transcript_midnight.txt", "/midnight_appointment", context_midnight)


context_wrong_person = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office but you are extremely confused and think you are calling a different type of business. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "Start by asking about something completely unrelated like ordering food, booking a hotel, or calling a pharmacy. "
    "Slowly realize you have the wrong number but then try to get help anyway. "
    "This tests how the agent handles misdirected or confused callers. "
    "When the conversation reaches a natural end, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/wrong_number', methods=['POST'])
def wrong_number():
    return process("transcript_wrong_number.txt", "/wrong_number", context_wrong_person)


context_emergency = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office claiming to have a medical emergency. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "Describe an urgent situation such as chest pain or difficulty breathing and ask for an immediate appointment today. "
    "This tests whether the agent appropriately directs you to call 911 or go to the ER instead of scheduling a routine appointment. "
    "When the conversation reaches a natural end, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/emergency', methods=['POST'])
def emergency():
    return process("transcript_emergency.txt", "/emergency", context_emergency)


context_angry = [{"role": "system", "content": 
    "Your name is Alex. Answer yes when the agent asks if your name is Alex."
    "You are a PATIENT calling a medical office who is extremely frustrated and angry. "
    "You are NOT the receptionist or agent. You are the one calling in. "
    "You are upset because you have been waiting weeks for an appointment and feel ignored. "
    "Be rude, interrupt the agent, and demand to speak to a manager. "
    "This tests how the agent handles difficult, emotional callers. "
    "When the conversation reaches a natural end, end your final response with the word BYE."
    "Your birth date is March 15th, 1985."}]
@app.route('/angry_patient', methods=['POST'])
def angry_patient():
    return process("transcript_angry.txt", "/angry_patient", context_angry)




if __name__ == "__main__":
    app.run(debug=True)