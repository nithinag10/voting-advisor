from dotenv import load_dotenv
import openai
import time
import streamlit as st


load_dotenv()

client = openai.OpenAI()

model = "gpt-4-1106-preview"  # "gpt-3.5-turbo-16k"


# == Hardcoded ids to be used once the first code run is done and the assistant was created
thread_id = "thread_Zgpm1mWxWmsGg1hdmgvYBII6"
assis_id = "asst_AfZrYUKXnenQ0KboHhHgUkko"

# Initialize all the session
if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = []

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


# Set up our front end page
st.set_page_config(page_title="Vote advisor. Be rational", page_icon=":books:")


# Define the function to process messages with citations
def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    print("Printing message")
    print(message)

    # Initialize the full response string
    full_response = ""

    # Process each content block in the message content list
    for content_block in message.content:
        # Start with the initial text of the content block
        message_content = content_block.text.value

        # Placeholder for collecting citations
        citations = []

        # Check for the existence of annotations in this content block
        if hasattr(content_block.text, 'annotations') and content_block.text.annotations:
            for index, annotation in enumerate(content_block.text.annotations):
                if hasattr(annotation, 'file_citation') and annotation.file_citation:
                    # Attempt to replace text with a footnote marker
                    try:
                        # Ensure the text exists in the content before replacing
                        if annotation.text in message_content:
                            message_content = message_content.replace(
                                annotation.text, f"[{index + 1}]")
                        else:
                            continue

                        # Retrieve the file details
                        file_id = annotation.file_citation.file_id
                        cited_file = client.files.retrieve(file_id)
                        filename = cited_file.filename if hasattr(cited_file, 'filename') else "Unknown File"
                        quote = annotation.file_citation.quote if annotation.file_citation.quote else "Reference"
                        citations.append(f"[{index + 1}] {quote} from {filename}")

                    except Exception as e:
                        print(f"Error processing annotation {index + 1}: {e}")
                        citations.append(f"[{index + 1}] Citation could not be retrieved")

        # Combine the content of this block with its citations
        full_response += f"{message_content}\n\n" + "\n".join(citations) + "\n"

    return full_response.strip()  # Remove any trailing newlines


st.title("Poll Pro")
st.write("""
This assistant uses GPT, an AI model developed by OpenAI. The model has been trained on a diverse and broad dataset, including a mixture of licensed data, data created by human trainers, and publicly available data. These sources may encompass government official documents, press releases, and official party documents. It's designed to provide informed responses based on this extensive corpus of text, although it's important to note that the responses generated do not represent official advice or legal guidance.
""")


def main():
    # Centering the start chat button in the main interface
    if st.button("Start Chatting...", key='start_chat_button'):
        st.session_state.start_chat = True
        # Create a new thread for this chat session
        chat_thread = client.beta.threads.create()
        st.session_state.thread_id = chat_thread.id
        st.write("Thread ID:", chat_thread.id)


    # Check sessions
    if st.session_state.start_chat:
        if "openai_model" not in st.session_state:
            st.session_state.openai_model = "gpt-4-1106-preview"
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Show existing messages if any...
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # chat input for the user
        if prompt := st.chat_input("What's new?"):
            # Add user message to the state and display on the screen
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # add the user's message to the existing thread
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id, role="user", content=prompt
            )

            # Create a run with additioal instructions
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=assis_id,
                instructions="""Always refer to the trained files and it is always the source of truth. If you are refering from other source always tell it may not be true . Reduce halluciantion""",
                tools=[{"type": "file_search"}],
            )

            # Show a spinner while the assistant is thinking...
            with st.spinner("Wait... Generating response..."):
                while run.status != "completed":
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id, run_id=run.id
                    )
                # Retrieve messages added by the assistant
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                # Process and display assis messages
                assistant_messages_for_run = [
                    message
                    for message in messages
                    if message.run_id == run.id and message.role == "assistant"
                ]

                for message in assistant_messages_for_run:
                    full_response = process_message_with_citations(message=message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )
                    with st.chat_message("assistant"):
                        st.markdown(full_response, unsafe_allow_html=True)


if __name__ == "__main__":
    main()