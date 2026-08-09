import logging

from dotenv import load_dotenv
from prompt import SYSTEM_PROMPT

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
    RunContext,
    function_tool,
)
from livekit.plugins import (
    murf,
    silero,
    google,
    deepgram,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db


logger = logging.getLogger("agent")

load_dotenv(".env.local")


def get_user_id(session: AgentSession, user_id: str = "") -> str:
    """
    Resolve the persistent user ID.

    Priority:
    1. Explicit user_id supplied by the tool call.
    2. LiveKit linked participant identity.
    3. Fallback to default_user.
    """

    if user_id:
        return user_id

    try:
        participant = session.room_io.linked_participant

        if participant:
            return participant.identity

    except Exception:
        logger.exception(
            "Could not resolve linked participant identity"
        )

    return "default_user"


class Assistant(Agent):
    def __init__(self, session: AgentSession) -> None:
        self._session = session

        super().__init__(
            instructions=SYSTEM_PROMPT
        )

    @function_tool
    async def lookup_user(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """
        Find an existing caller from the SQLite database.

        Args:
            user_id: Optional unique user ID.
            If not provided, the LiveKit participant identity
            will be used automatically.
        """

        resolved_uid = get_user_id(
            self._session,
            user_id,
        )

        logger.info(
            "Looking up user with ID: %s",
            resolved_uid,
        )

        user = db.get_user(resolved_uid)

        if user:
            logger.info(
                "User found: %s",
                resolved_uid,
            )

            return (
                f"User found: "
                f"ID={user['user_id']}, "
                f"Name={user['name']}, "
                f"Language Preference={user['language_preference']}, "
                f"Facts={user['facts']}, "
                f"Last Interaction={user['last_interaction']}"
            )

        logger.info(
            "No user found for ID: %s",
            resolved_uid,
        )

        return "No user found with this ID."

    @function_tool
    async def save_user(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: str,
        last_interaction: str,
        user_id: str = "",
    ) -> str:
        """
        Save or update caller information in SQLite.

        The agent must explicitly ask for permission
        before saving user information.

        Args:
            name: The caller's name.
            language_preference:
                English, Hindi, or Hinglish.
            facts:
                Relevant non-sensitive information about
                the caller.
            last_interaction:
                Summary of the latest interaction.
            user_id:
                Optional unique user ID.
        """

        resolved_uid = get_user_id(
            self._session,
            user_id,
        )

        logger.info(
            "Saving user with ID: %s",
            resolved_uid,
        )

        db.save_user_db(
            user_id=resolved_uid,
            name=name,
            language_preference=language_preference,
            facts=facts,
            last_interaction=last_interaction,
        )

        logger.info(
            "User successfully saved: %s",
            resolved_uid,
        )

        return (
            f"User details successfully saved "
            f"for ID {resolved_uid}."
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Create the voice AI pipeline
    session = AgentSession(

        # Speech-to-text
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        # LLM
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # Text-to-speech
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        # Turn detection
        turn_detection=MultilingualModel(),

        # Voice activity detection
        vad=ctx.proc.userdata["vad"],

        # Generate response while waiting for end of turn
        preemptive_generation=True,
    )

    # Start the session
    await session.start(
        agent=Assistant(session),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Connect to the LiveKit room
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
