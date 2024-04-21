import streamlit as st
import openai

# Load your OpenAI API key
openai.api_key = 'your-openai-api-key'

# Set up your assistant ID
ASSISTANT_ID = "asst_AfZrYUKXnenQ0KboHhHgUkko"

# Page configuration
st.set_page_config(page_title="Voting Advisor", page_icon=":ballot_box:")

# Title and description
st.title("Voting Advisor")
st.write("Ask any questions you have about voting and I'll try to help!")

# Input from user
user_input = st.text_input("Ask a question about voting:")

if user_input:
    # OpenAI Assistant API call
    response = openai.ChatCompletion.create(
        model="gpt-4",  # or another model that your assistant uses
        messages=[{"role": "user", "content": user_input}],
        assistant_id=ASSISTANT_ID,
    )

    # Display the response
    if response['choices']:
        answer = response['choices'][0]['message']['content']
        st.write("Answer:", answer)
    else:
        st.error("Sorry, I couldn't generate a response. Try again.")

# Run this script using: streamlit run app.py
