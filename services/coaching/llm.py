from services.config.workout_config import PROMPT

class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.feedback_history = []  # feedback history from llm is stored here
        self.system_prompt = PROMPT # This becomes the system instruction sent to the LLM.
        self.session_context = ""   # short summary of the user's recent sessions, set via set_session_context()

    def set_session_context(self, recent_sessions):
        """recent_sessions: list of sqlite3.Row objects, as returned by get_recent_sessions()."""
        if not recent_sessions:
            self.session_context = ""
            return

        lines = [
            f"- {r['exercise_name']}: {r['reps']} reps, form score {r['form_score']}%"
            for r in recent_sessions
        ]
        self.session_context = "User's recent sessions:\n" + "\n".join(lines)

    def give_feedback(self, event, issue):
        prompt = f"Event: {event}"

        if issue:
            prompt += f". Form Issue: {issue}"

        system_content = self.system_prompt
        if self.session_context:
            system_content += "\n\n" + self.session_context

        messages = [                    # Creates the full conversation list sent to the LLM.
            {"role": "system", "content": system_content},
            *self.feedback_history[-10:],
            {"role": "user", "content": prompt}
        ]

        # pass the messages list to the client to get the response
        response = self.client.chat.completions.create(
            model = "llama-3.3-70b-versatile",
            messages = messages,
            temperature = 0.4
        )
        
        # Extracting AI Response
        text_feedback = response.choices[0].message.content.strip()
        self.feedback_history.append({"role": "assistant", "content": text_feedback})

        return text_feedback