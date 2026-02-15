import streamlit as st
import os
import google.generativeai as genai
from PIL import Image

if 'health_profile' not in st.session_state:
    st.session_state.health_profile = {
    'goals': '',
    'conditions': '',
    'routines': '',
    'preferences': '',
    'restrictions': '',
    'budget': '150-200',
    'currency': 'USD'
    }

def get_gemini_response(input_prompt, image_data=None):
    model = genai.GenerativeModel('gemini-2.5-flash')

    content = [input_prompt]

    if image_data:
        content.extend(image_data)
    
    try:
        response = model.generate_content(content)
        return response.text
    except Exception as e:
        error_str = str(e)
        
        # Check for common quota-related error indicators
        if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
            return """🚫 **API Daily Quota Reached**

You've hit the Google Gemini API free tier limit of **20 requests per day**.

**What you can do:**

1. **Wait until tomorrow** - Your quota resets daily. Come back in a few hours!
2. **Upgrade to Google Cloud Paid Plan** - Get thousands of requests per day:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable billing on your project
   - Much higher limits for development & testing

3. **Contact Support** - Check your Google Cloud billing page for more details

*Your quota will reset at 00:00 UTC tomorrow*"""
        
        return f"Error generating response: {str(e)}"
    
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [{
            "mime_type": uploaded_file.type,
            "data": bytes_data
        }]
        return image_parts
    return None


st.set_page_config(page_title="AI Health Coach", layout="wide")
st.header("👾 AI Health Coach")

with st.sidebar:
    st.subheader("Your Health Profile")

    health_goals = st.text_area("Health Goals", placeholder="e.g., Weight loss, muscle gain, improved energy, better sleep")

    medical_conditions = st.text_area("Medical Conditions", placeholder="e.g., Diabetes, hypertension, food allergies, digestive issues")

    fitness_routines = st.text_area("Current Fitness Routines", placeholder="e.g., Running 3x/week, yoga 2x/week, strength training 4x/week")

    food_preferences = st.text_area("Food Preferences", placeholder="e.g., Vegetarian, vegan, low-carb, high-protein, Mediterranean diet")

    restrictions = st.text_area("Dietary Restrictions", placeholder="e.g., Gluten-free, dairy-free, nut allergies, low-sodium")

    col1, col2 = st.columns(2)
    with col1:
        currency = st.selectbox("Currency Type", 
            ["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "JPY (¥)"],
            index=["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "JPY (¥)"].index(st.session_state.health_profile['currency'] if st.session_state.health_profile['currency'] in ["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "JPY (¥)"] else "USD ($)"))
    
    with col2:
        budget = st.selectbox("Monthly Food Budget", 
            ["50-100", "100-150", "150-200", "200-300", "300+"],
            index=["50-100", "100-150", "150-200", "200-300", "300+"].index(st.session_state.health_profile['budget']))

    if st.button("Update Profile"):
        st.session_state.health_profile = {
            'goals': health_goals,
            'conditions': medical_conditions,
            'routines': fitness_routines,
            'preferences': food_preferences,
            'restrictions': restrictions,
            'budget': budget,
            'currency': currency
        }
        st.success("Health profile updated!")


tab1, tab2, tab3, tab4 = st.tabs(["🏋️ workout planning", "🏋️‍♂️ meal planning", "🍎 food analysis", "🧘‍♀️ health insights"])

with tab1:
    st.subheader("🏋️ Personalized Workout Planning")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Your Fitness Details")
        fitness_level = st.selectbox("Current Fitness Level", ["None", "Beginner", "Intermediate", "Advanced"], index=0)
        
        available_equipment = st.multiselect(
            "Available Equipment",
            ["None", "Dumbbells", "Barbell", "Gym Membership", "Only Bodyweight", "Resistance Bands", "Treadmill", "Stationary Bike"],
            default=["None"]
        )
        
        workout_frequency = st.selectbox("Workouts Per Week", ["None", "2-3 days", "3-4 days", "4-5 days", "5-6 days"], index=0)
        
        session_duration = st.selectbox("Session Duration", ["None", "20-30 minutes", "30-45 minutes", "45-60 minutes", "60+ minutes"], index=0)

    with col2:
        st.write("### Your Health Profile")
        st.json(st.session_state.health_profile)

    workout_input = st.text_area(
        "Additional Workout Preferences:",
        placeholder="E.g., I have 45 minutes available, no gym access, want to improve strength and endurance"
    )

    uploaded_workout_image = st.file_uploader("Upload an image (optional) — form/progress photo", type=["jpg", "jpeg", "png"])

    if uploaded_workout_image is not None:
        try:
            img = Image.open(uploaded_workout_image)
            st.image(img, caption="Preview (please confirm to use this image)", use_column_width=True)
        except Exception:
            st.write("Unable to preview the image.")

        if 'workout_image_confirmed' not in st.session_state:
            st.session_state['workout_image_confirmed'] = False

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Confirm Image", key="confirm_img"):
                st.session_state['confirmed_workout_image'] = uploaded_workout_image
                st.session_state['workout_image_confirmed'] = True
                st.success("Image confirmed. You can now use Get Workout Plan & Analysis.")
        with c2:
            if st.button("Remove Image", key="remove_img"):
                if 'confirmed_workout_image' in st.session_state:
                    del st.session_state['confirmed_workout_image']
                st.session_state['workout_image_confirmed'] = False
                st.info("Image removed. Upload a new image if needed.")

    workout_question = st.text_area(
        "Ask a specific workout/physique question:",
        placeholder="E.g., How can I build my chest? Please check my bench press form (optional image upload)."
    )

    image_for_analysis = st.session_state.get('confirmed_workout_image') if st.session_state.get('workout_image_confirmed') else None

    include_youtube = st.checkbox("Include YouTube recommendations (toggle off to skip)", value=False)

    if st.button("Get Workout Plan & Analysis"):
        equipment_provided = bool(available_equipment and not (len(available_equipment) == 1 and available_equipment[0] == 'None'))
        details_provided = (fitness_level != 'None') or equipment_provided or (workout_frequency != 'None') or (session_duration != 'None')

        if not (details_provided or workout_question or image_for_analysis):
            st.warning("Please provide some fitness details, a question, or confirm an uploaded image to analyze.")
        else:
            with st.spinner("Preparing personalized workout plan and analysis..."):
                image_data = input_image_setup(image_for_analysis)

                display_fitness_level = fitness_level if fitness_level != 'None' else 'Not provided'
                display_equipment = ', '.join([e for e in available_equipment if e != 'None']) if equipment_provided else 'Not provided'
                display_workout_frequency = workout_frequency if workout_frequency != 'None' else 'Not provided'
                display_session_duration = session_duration if session_duration != 'None' else 'Not provided'

                prompt = f"""
                You are a qualified fitness coach and nutritionist. Consider the user's fitness details, health profile, budget and any uploaded image.

                Fitness Details:
                - Fitness Level: {display_fitness_level}
                - Available Equipment: {display_equipment}
                - Workouts Per Week: {display_workout_frequency}
                - Session Duration: {display_session_duration}

                Health Profile:
                - Goals: {st.session_state.health_profile.get('goals','')}
                - Medical Conditions: {st.session_state.health_profile.get('conditions','')}
                - Current Routines: {st.session_state.health_profile.get('routines','')}
                - Food Preferences: {st.session_state.health_profile.get('preferences','')}
                - Dietary Restrictions: {st.session_state.health_profile.get('restrictions','')}
                - Monthly Budget: {st.session_state.health_profile.get('budget','')} {st.session_state.health_profile.get('currency','')}

                User additional preferences: {workout_input if workout_input else 'None provided'}
                User question: {workout_question if workout_question else 'No specific question provided.'}

                If an image is provided, analyze posture/form/progress and clearly state limitations of visual-only assessment.

                Please provide a single combined response with:
                1) A weekly workout schedule tailored to the user's details.
                2) For key exercises: sets, reps, rest, form cues, and progressions.
                3) Warm-up and cool-down routines.
                4) If an image is provided, an image-based assessment with form corrections and progress commentary.
                5) Diet suggestions for muscle building or the user's goals, with meal examples and approximate costs in the user's currency.
                6) 3 recommended YouTube videos (title, channel, URL if available) or precise search queries and brief reasons to watch each. ONLY include YouTube recommendations if the user requested them.
                7) Safety precautions and recovery guidance.
                8) Clear next steps the user can take this week.

                At the top of your response include a SUMMARY block with these exact keys (use these labels exactly):
                Summary:, Main Focus:, Weekly Plan (one-line):, Diet Summary:, Estimated Weekly Cost:

                Format the answer with headings, short sections, bullet points, and include the SUMMARY block at the very top.
                """

                response = get_gemini_response(prompt, image_data)

                import re
                summary_keys = ["Summary:", "Main Focus:", "Weekly Plan (one-line):", "Diet Summary:", "Estimated Weekly Cost:"]
                summary_data = {}
                for key in summary_keys:
                    pattern = re.escape(key) + r"\s*(.*)"
                    m = re.search(pattern, response, flags=re.IGNORECASE)
                    summary_data[key.rstrip(':')] = m.group(1).strip() if m else "Not provided"

                st.subheader("Quick Summary")
                try:
                    st.table([summary_data])
                except Exception:
                    st.write(summary_data)

                st.subheader("Workout Plan & Analysis")
                st.markdown(response)

                if include_youtube:
                    urls = re.findall(r"https?://\S+", response)
                    yt_urls = [u for u in urls if 'youtube.com' in u or 'youtu.be' in u]
                    for u in yt_urls:
                        try:
                            st.video(u)
                        except Exception:
                            pass

                st.download_button(
                    label="Download Full Report",
                    data=response,
                    file_name="workout_plan_and_analysis.txt",
                    mime="text/plain"
                )

with tab2:
    st.subheader("🍽️ Personalized Meal Planning")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### your current needs")
        user_input = st.text_area("Describe your current health and fitness needs:", placeholder="E.g., I want to lose weight and improve my energy levels. I prefer vegetarian meals and have no dietary restrictions.")

    with col2:
        st.write("### your health profile")
        st.json(st.session_state.health_profile)

    if st.button("Generate personalized meal plan"):
        if not any(st.session_state.health_profile.values()):
            st.warning("Please fill out your health profile in the sidebar before generating a meal plan.")
        else:
            with st.spinner("Generating your personalized meal plan..."):

                prompt = f""" 
                create a personalized meal plan based on the following health profile:

                Health Goals: {st.session_state.health_profile['goals']}
                Medical Conditions: {st.session_state.health_profile['conditions']}
                Current Fitness Routines: {st.session_state.health_profile['routines']}
                Food Preferences: {st.session_state.health_profile['preferences']}
                Dietary Restrictions: {st.session_state.health_profile['restrictions']}
                Monthly Food Budget: {st.session_state.health_profile['budget']} {st.session_state.health_profile['currency']}

                Additional requirements: {user_input if user_input else "None provided"}

provide:
1. A 7-day meal plan with breakfast, lunch, dinner, and snacks - ALL meals must be budget-friendly and fit within the monthly budget
2. nutritional breakdown for each day (calories, macros)
3. contextual explanation for why each meal was chosen and how it fits the budget
4. shopping list organized by category with estimated costs in {st.session_state.health_profile['currency']} for each item
5. preparation tips and time estimates for each meal
6. cost breakdown per day and per week in {st.session_state.health_profile['currency']}
7. money-saving tips on ingredients without compromising nutrition

format the response in a clear and organized manner, using bullet points, tables, or sections as needed.
"""
                
                
                response: str = get_gemini_response(prompt)

                st.subheader("Generated Meal Plan")
                st.markdown(response)

                st.download_button(
                    label="Download Meal Plan",
                    data=response,
                    file_name="personalized_meal_plan.txt",
                    mime="text/plain"
                )

with tab3:
    st.subheader("🍎 Food Analysis")

    uploaded_file = st.file_uploader("Upload an image of your meal for analysis", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Meal Image", use_column_width=True)

        if st.button("Analyze Meal"):
            with st.spinner("Analyzing your meal..."):
                image_data = input_image_setup(uploaded_file)

                prompt = f"""
                you are a nutrition expert. Analyze the meal in the provided image. 
                
                provide the following information:
                1. Estimated calorie content
                2. Macronutrient breakdown (carbs, protein, fat)
                3. potential health benefits of the meal
                4. any concerns based on common dietary restrictions (e.g., allergens, high sugar content)
                5. suggested portion size recommendations based on general dietary guidelines

                if the food items in the image are not clearly identifiable, provide your best guess based on visual cues and explain your reasoning.
                """

                response = get_gemini_response(prompt, image_data)
                st.subheader("Meal Analysis results")
                st.markdown(response)

with tab4:
    st.subheader("🧘‍♀️ Health Insights")

    health_query = st.text_area("Ask any health/nutrition-related question:", 
                                placeholder="E.g., What are some effective strategies for improving sleep quality?")
    
    if st.button("Get Health Insights"):
        if not health_query:
            st.warning("Please enter a health-related question to get insights.")
        else:
            with st.spinner("researching your question..."):
                prompt = f"""
                you are a knowledgeable health and nutrition expert. Provide a comprehensive answer to the following question:

                {health_query}

                consider the user's health profile:
                {st.session_state.health_profile}

                include:
                1. clear explanation of the topic
                2. practical tips or strategies related to the question
                3. any relevant precautions or considerations based on common health conditions or dietary restrictions
                4. references to credible sources or studies if applicable
                5. suggested foods/supplements/exercises if relevant to the question

                format the response in a clear and organized manner, using bullet points, sections, or examples as needed, and maintain a professional and helpful tone.
                """

                response = get_gemini_response(prompt)
                st.subheader("Health Insights")
                st.markdown(response)