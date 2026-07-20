import streamlit as st

st.title("Welcome to Archi!")
st.write("This is an academic chatbot to help with your flowchart, academic advising, and GPA optimization!")

chat = st.text_input("Ask Archi...")

if chat:
    st.success(f"Welcome to Archi {chat}!")

age = st.slider("Select your age:", 0, 100, 25)
st.write(f"You selected: **{age}** years old.")