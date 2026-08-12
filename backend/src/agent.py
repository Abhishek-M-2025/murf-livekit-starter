import json
import logging

from dotenv import load_dotenv
from prompt import SYSTEM_PROMPT, OUTBOUND_SYSTEM_PROMPT

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
import health_facility_service


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
    def __init__(
        self,
        session: AgentSession = None,
        instructions: str = SYSTEM_PROMPT,
    ) -> None:
        self._session = session

        super().__init__(
            instructions=instructions
        )

    @function_tool
    async def lookup_user(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """
        Find an existing caller from the SQLite database.
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

    @function_tool
    async def find_nearest_health_facility(
        self,
        context: RunContext,
        location_or_district: str,
    ) -> str:
        """
        Look up the nearest government health facilities
        or Primary Health Centres (PHC) in a given location
        or district.
        """

        logger.info(
            "Looking up nearest health facilities for "
            "location_or_district: %s",
            location_or_district,
        )

        try:
            result = await health_facility_service.get_nearest_facilities(
                location_or_district
            )

            source = result.get("source", "none")
            facilities = result.get("facilities", [])

            if source == "none" or not facilities:
                return (
                    "FAIL: No verified health facilities "
                    "found or API error."
                )

            source_desc = (
                "live database (fetched via government API)"
                if source == "live"
                else "local fallback database"
            )

            output = (
                f"SOURCE_INFO: This data is from the "
                f"{source_desc}.\n"
            )

            output += (
                f"FACILITIES_FOUND in "
                f"{location_or_district.title()}:\n"
            )

            for idx, fac in enumerate(facilities, 1):
                output += (
                    f"{idx}. Name: {fac['name']}\n"
                    f"   Type: {fac['type']}\n"
                    f"   District: {fac['district']}\n"
                    f"   State: {fac['state']}\n"
                    f"   Address: {fac['address']}\n\n"
                )

            return output.strip()

        except Exception:
            logger.exception(
                "Error during nearest health facility lookup"
            )

            return "FAIL: Exception occurred during lookup."

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        reason: str,
        short_summary: str,
        checked_info: str,
        urgency: str,
        language: str,
        preferred_followup: str = "phone",
    ) -> str:
        """
        Create a human escalation request when the user has serious red-flag symptoms
        or asks to diagnose a disease, AND they have given explicit consent.

        Args:
            reason: The main reason/trigger for escalation (e.g., 'Severe chest pain', 'Diagnosis request').
            short_summary: A brief description of the symptoms or request (e.g., 'Severe chest pain for 30 minutes').
            checked_info: Safe, relevant details, excluding any private sensitive data (e.g., OTPs, passwords, PINs, card numbers).
            urgency: The urgency level of the request ('high', 'medium', 'low').
            language: The language used by the caller ('Hindi', 'English', 'Hinglish').
            preferred_followup: The preferred followup channel, default 'phone'.
        """
        logger.info("create_escalation tool called with reason: %s, urgency: %s", reason, urgency)
        try:
            reference_id = db.create_escalation(
                reason=reason,
                short_summary=short_summary,
                checked_info=checked_info,
                urgency=urgency,
                language=language,
                preferred_followup=preferred_followup,
            )
            return f"SUCCESS: Escalation created. Reference ID is {reference_id}."
        except Exception as e:
            logger.exception("Error in create_escalation tool")
            return f"FAIL: Could not create escalation. Error: {str(e)}"


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # ---------------------------------------------------------
    # Detect outbound Day 6 session
    # ---------------------------------------------------------

    is_outbound = False
    user_name = "there"

    try:
        metadata = ctx.job.metadata

        if metadata:
            metadata = json.loads(metadata)

            is_outbound = (
                metadata.get("call_type")
                == "medication_reminder"
            )

            user_name = metadata.get(
                "user_name",
                "there",
            )

            logger.info(
                "Job metadata: %s",
                metadata,
            )

    except Exception:
        logger.exception(
            "Failed to parse job metadata"
        )

    logger.info(
        "Outbound session: %s",
        is_outbound,
    )

    # ---------------------------------------------------------
    # Voice AI pipeline
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Select prompt
    # ---------------------------------------------------------

    instructions = (
        OUTBOUND_SYSTEM_PROMPT
        if is_outbound
        else SYSTEM_PROMPT
    )

    # ---------------------------------------------------------
    # Start the session
    # ---------------------------------------------------------

    await session.start(
        agent=Assistant(
            session=session,
            instructions=instructions,
        ),
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

    # ---------------------------------------------------------
    # Connect to LiveKit room
    # ---------------------------------------------------------

    await ctx.connect()

    logger.info(
        "Agent connected to room: %s",
        ctx.room.name,
    )

    # ---------------------------------------------------------
    # DAY 6 — Automatic outbound greeting
    # ---------------------------------------------------------

    if is_outbound:

        logger.info(
            "Outbound medication reminder call detected."
        )

        logger.info(
            "Waiting for SIP participant to join..."
        )

        try:
            participant = await ctx.wait_for_participant()

            logger.info(
                "SIP participant joined: %s",
                participant.identity,
            )

            # Give the SIP connection a short moment
            # to become fully ready for two-way audio.
            await asyncio.sleep(0.5)

            logger.info(
                "Starting automatic outbound greeting..."
            )

            await session.generate_reply(
                instructions=(
                    f"Start the outbound medication reminder call "
                    f"with the patient named {user_name}. "
                    "Speak first without waiting for the patient. "
                    "Introduce yourself as Anisha, explain that "
                    "this is an automated medication reminder call, "
                    "ask if this is a good time to talk, and clearly "
                    "tell the patient they can say stop if they "
                    "do not want further calls."
                )
            )

            logger.info(
                "Outbound greeting triggered successfully."
            )

        except Exception:
            logger.exception(
                "Failed to start outbound greeting."
            )


if __name__ == "__main__":
    cli.run_app(server)
