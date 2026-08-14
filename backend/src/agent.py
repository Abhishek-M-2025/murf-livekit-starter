import asyncio
import json
import logging
import threading
import uuid
from typing import Any, Optional

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


# =========================================================
# SESSION HELPERS
# =========================================================

def set_session_flag(
    session: Optional[AgentSession],
    key: str,
    value: Any,
) -> None:
    if session is None:
        return

    try:
        session.userdata[key] = value
    except (AttributeError, ValueError):
        if not hasattr(session, "_custom_userdata"):
            session._custom_userdata = {}
        session._custom_userdata[key] = value


def get_session_flag(
    session: Optional[AgentSession],
    key: str,
    default: Any = None,
) -> Any:
    if session is None:
        return default

    try:
        return session.userdata.get(key, default)
    except (AttributeError, ValueError):
        if hasattr(session, "_custom_userdata"):
            return session._custom_userdata.get(key, default)

    return default


def get_user_id(
    session: AgentSession,
    user_id: str = "",
) -> str:

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


# =========================================================
# DAY 9 SPECIALIST
# CLINIC & APPOINTMENT SPECIALIST - SAMAR
# =========================================================

class ClinicAppointmentSpecialist(Agent):

    def __init__(self, chat_ctx=None) -> None:

        super().__init__(
            instructions="""
You are Samar, the Clinic & Appointment Specialist.

Your job is to help the user with specialist appointments,
clinic appointments, and scheduling visits to health facilities.

You are NOT a doctor and you are NOT a specific medical specialist
such as a cardiologist. You are the specialist appointment agent.

The main assistant, Anisa, has already spoken with the user before
transferring the conversation to you.

IMPORTANT:

- Continue from the previous conversation.
- Do NOT ask the user to repeat information they already provided.
- First introduce yourself briefly as Samar, the Clinic & Appointment Specialist.
- Acknowledge the reason for the handoff.
- If the user has already said which medical specialist they need,
  do not ask for the specialist type again.
- If the user only asked to speak with a specialist and has not said
  which type, ask which medical specialist they want to see.
- Examples include cardiologist, dermatologist, orthopedist,
  gynecologist, pediatrician, etc.
- After knowing the specialist type, ask for the preferred location
  if it is not already known.
- Then ask for the preferred appointment date.
- Then ask for the preferred appointment time if needed.
- Collect only the information needed to arrange the appointment.
- Do not claim that an appointment is actually booked unless a real
  booking system confirms the booking.
- If no real booking system is available, clearly say that you can
  help identify and plan the appointment but cannot falsely confirm
  a booking.
- Be concise, natural, and professional.
- Continue in the user's language when possible, including Hindi,
  Hinglish, or English.
""",
            chat_ctx=chat_ctx,

            # Samar's voice
            tts=murf.TTS(
                voice="Samar",
                style="Conversational",
                model="FALCON",
                tokenizer=tokenize.basic.SentenceTokenizer(
                    min_sentence_len=2
                ),
                text_pacing=True,
            ),
        )

    async def on_enter(self) -> None:

        logger.info(
            "Clinic & Appointment Specialist Samar is now active."
        )

        await self.session.generate_reply(
            instructions=(
                "Introduce yourself briefly as Samar, the Clinic "
                "and Appointment Specialist. Tell the user you are "
                "continuing from Anisa's conversation. Do not ask "
                "them to repeat what they already said. If the "
                "medical specialist type is already known from the "
                "conversation, continue from it. Otherwise ask "
                "which medical specialist they would like to see."
            )
        )


# =========================================================
# ASSISTANT
# =========================================================

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

    # -----------------------------------------------------
    # DAY 9 HANDOFF
    # -----------------------------------------------------

    @function_tool
    async def transfer_to_clinic_specialist(
        self,
        context: RunContext,
    ):
        """
        Transfer the user to Samar, the Clinic & Appointment
        Specialist, when the user needs help with a specialist
        appointment, clinic appointment, scheduling, or planning
        a visit to a health facility.
        """

        logger.info(
            "DAY 9 HANDOFF: Anisa -> Samar"
        )

        # Tell the user before switching.
        await self.session.generate_reply(
            instructions=(
                'Say exactly: "I\'ll connect you with our clinic '
                'and appointment specialist." Keep it brief.'
            )
        )

        # Pass the previous conversation to Samar.
        # Previous system instructions are excluded so Samar uses
        # his own specialist instructions.
        return ClinicAppointmentSpecialist(
            chat_ctx=self.chat_ctx.copy(
                exclude_instructions=True
            )
        )

    # -----------------------------------------------------
    # LOOKUP USER
    # -----------------------------------------------------

    @function_tool
    async def lookup_user(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:

        resolved_uid = get_user_id(
            self._session,
            user_id,
        )

        logger.info(
            "Looking up user: %s",
            resolved_uid,
        )

        user = db.get_user(resolved_uid)

        if user:
            return (
                f"User found: "
                f"ID={user['user_id']}, "
                f"Name={user['name']}, "
                f"Language Preference={user['language_preference']}, "
                f"Facts={user['facts']}, "
                f"Last Interaction={user['last_interaction']}"
            )

        return "No user found with this ID."

    # -----------------------------------------------------
    # SAVE USER
    # -----------------------------------------------------

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

        resolved_uid = get_user_id(
            self._session,
            user_id,
        )

        logger.info(
            "Saving user: %s",
            resolved_uid,
        )

        db.save_user_db(
            user_id=resolved_uid,
            name=name,
            language_preference=language_preference,
            facts=facts,
            last_interaction=last_interaction,
        )

        return (
            f"User details successfully saved "
            f"for ID {resolved_uid}."
        )

    # -----------------------------------------------------
    # HEALTH FACILITY
    # -----------------------------------------------------

    @function_tool
    async def find_nearest_health_facility(
        self,
        context: RunContext,
        location_or_district: str,
    ) -> str:

        logger.info(
            "Looking up health facilities for: %s",
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

            set_session_flag(
                self._session,
                "facility_lookup_called",
                True,
            )

            return output.strip()

        except Exception:
            logger.exception(
                "Error during nearest health facility lookup"
            )
            return "FAIL: Exception occurred during lookup."

    # -----------------------------------------------------
    # ESCALATION
    # -----------------------------------------------------

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

        logger.info(
            "Creating escalation: reason=%s urgency=%s",
            reason,
            urgency,
        )

        try:
            reference_id = db.create_escalation(
                reason=reason,
                short_summary=short_summary,
                checked_info=checked_info,
                urgency=urgency,
                language=language,
                preferred_followup=preferred_followup,
            )

            set_session_flag(
                self._session,
                "has_escalated",
                True,
            )

            return (
                f"SUCCESS: Escalation created. "
                f"Reference ID is {reference_id}."
            )

        except Exception as e:
            logger.exception(
                "Error in create_escalation tool"
            )

            return (
                f"FAIL: Could not create escalation. "
                f"Error: {str(e)}"
            )


# =========================================================
# SERVER
# =========================================================

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


# =========================================================
# LIVEKIT SESSION
# =========================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # -----------------------------------------------------
    # CALL METADATA
    # -----------------------------------------------------

    is_outbound = False
    user_name = "there"
    call_id = ""

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

            call_id = metadata.get(
                "call_id",
                "",
            )

            logger.info(
                "Job metadata: %s",
                metadata,
            )

    except Exception:
        logger.exception(
            "Failed to parse job metadata"
        )

    # -----------------------------------------------------
    # CALL ID
    # -----------------------------------------------------

    if not call_id:
        call_id = f"call_browser_{uuid.uuid4().hex}"

    logger.info(
        "Session call_id=%s outbound=%s",
        call_id,
        is_outbound,
    )

    # -----------------------------------------------------
    # START AS IN_PROGRESS
    # -----------------------------------------------------

    db.create_call(
        call_id,
        "outbound" if is_outbound else "browser",
        "in_progress",
    )

    # =====================================================
    # VOICE PIPELINE
    # =====================================================

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],

        preemptive_generation=True,
    )

    # =====================================================
    # SESSION FLAGS
    # =====================================================

    set_session_flag(session, "call_id", call_id)
    set_session_flag(session, "has_escalated", False)
    set_session_flag(session, "facility_lookup_called", False)
    set_session_flag(session, "user_spoke", False)
    set_session_flag(session, "agent_responded_to_user", False)

    # =====================================================
    # USER SPEECH
    # =====================================================

    @session.on("user_input_transcribed")
    def on_user_input(ev):

        if ev.text and ev.text.strip():

            set_session_flag(
                session,
                "user_spoke",
                True,
            )

            logger.info(
                "USER SPOKE: %s",
                ev.text,
            )

    # =====================================================
    # AGENT RESPONSE
    # =====================================================

    @session.on("conversation_item_added")
    def on_item_added(ev):

        try:
            if ev.item.role == "assistant":

                set_session_flag(
                    session,
                    "agent_responded_to_user",
                    True,
                )

                logger.info(
                    "AGENT RESPONSE DETECTED"
                )

        except Exception:
            logger.exception(
                "Error tracking conversation item"
            )

    # =====================================================
    # SHUTDOWN / FINAL STATUS
    # =====================================================

    async def on_shutdown():

        logger.info(
            "CALL SHUTDOWN: evaluating final status"
        )

        user_spoke = get_session_flag(
            session,
            "user_spoke",
            False,
        )

        agent_responded = get_session_flag(
            session,
            "agent_responded_to_user",
            False,
        )

        facility_lookup = get_session_flag(
            session,
            "facility_lookup_called",
            False,
        )

        has_escalated = get_session_flag(
            session,
            "has_escalated",
            False,
        )

        logger.info(
            "FINAL CHECK: user_spoke=%s "
            "agent_responded=%s "
            "facility_lookup=%s "
            "escalated=%s",
            user_spoke,
            agent_responded,
            facility_lookup,
            has_escalated,
        )

        # -------------------------------------------------
        # Browser call
        # -------------------------------------------------

        if not is_outbound:

            success = (
                user_spoke
                and agent_responded
            )

            if facility_lookup or has_escalated:
                success = True

        # -------------------------------------------------
        # Outbound call
        # -------------------------------------------------

        else:

            messages = session.chat_ctx.messages

            user_turns = [
                m for m in messages
                if m.role == "user"
            ]

            assistant_turns = [
                m for m in messages
                if m.role == "assistant"
            ]

            success = bool(
                user_turns
                and assistant_turns
            )

        # -------------------------------------------------
        # FINAL STATUS
        # -------------------------------------------------

        status = (
            "success"
            if success
            else "failed"
        )

        db.update_call_status(
            call_id,
            status,
        )

        logger.info(
            "FINAL CALL STATUS: %s | call_id=%s",
            status,
            call_id,
        )

    ctx.add_shutdown_callback(
        on_shutdown
    )

    # =====================================================
    # PROMPT
    # =====================================================

    instructions = (
        OUTBOUND_SYSTEM_PROMPT
        if is_outbound
        else SYSTEM_PROMPT
    )

    # =====================================================
    # START SESSION
    # =====================================================

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

    # =====================================================
    # CONNECT ROOM
    # =====================================================

    await ctx.connect()

    logger.info(
        "Agent connected to room: %s",
        ctx.room.name,
    )

    # =====================================================
    # OUTBOUND GREETING
    # =====================================================

    if is_outbound:

        logger.info(
            "Outbound medication reminder call detected."
        )

        try:

            participant = await ctx.wait_for_participant()

            logger.info(
                "SIP participant joined: %s",
                participant.identity,
            )

            await asyncio.sleep(0.5)

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


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    def run_trigger_server():

        try:

            from outbound_call import start_trigger_server

            logger.info(
                "Starting background outbound call "
                "trigger server on port 5001..."
            )

            start_trigger_server(5001)

        except Exception:

            logger.exception(
                "Failed to start background trigger server"
            )

    threading.Thread(
        target=run_trigger_server,
        daemon=True,
    ).start()

    cli.run_app(server)
