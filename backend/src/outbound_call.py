import os
import logging
import asyncio
import json
import time

from dotenv import load_dotenv
from livekit import api
from aiohttp import web


load_dotenv(".env.local")

logger = logging.getLogger("outbound_call")


def extract_sip_user(destination: str) -> str:
    """
    Extract the SIP user from a full SIP URI.

    Example:
        sip:abhishek2026@sip.linphone.org
        -> abhishek2026

        +1234567890
        -> +1234567890
    """

    destination = destination.strip()

    if destination.startswith("sip:"):
        destination = destination[4:]
    elif destination.startswith("sips:"):
        destination = destination[5:]

    if "@" in destination:
        destination = destination.split("@")[0]

    return destination


async def make_outbound_call(
    destination: str,
    room_name: str,
    user_name: str = "",
    call_type: str = "medication_reminder",
    reminder: str = "Medication reminder",
) -> tuple[bool, str]:
    """
    Trigger an outbound SIP call using LiveKit.

    1. Dispatch the agent to the room.
    2. Create the SIP participant.
    3. Wait until the call is answered.
    """

    livekit_url = os.getenv("LIVEKIT_URL")
    livekit_api_key = os.getenv("LIVEKIT_API_KEY")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
    sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")

    # Validate LiveKit credentials
    if not livekit_url or not livekit_api_key or not livekit_api_secret:
        err_msg = (
            "LiveKit credentials "
            "(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) "
            "must be set."
        )

        logger.error(err_msg)
        return False, err_msg

    # Validate SIP trunk
    if not sip_trunk_id:
        err_msg = "LIVEKIT_SIP_TRUNK_ID must be set."

        logger.error(err_msg)
        return False, err_msg

    # Convert full SIP URI to SIP user
    sip_call_to = extract_sip_user(destination)

    logger.info(
        "Initiating outbound call to %s "
        "(formatted destination: %s) in room %s...",
        destination,
        sip_call_to,
        room_name,
    )

    lkapi = api.LiveKitAPI(
        url=livekit_url,
        api_key=livekit_api_key,
        api_secret=livekit_api_secret,
    )

    try:
        # ---------------------------------------------------------
        # 1. Dispatch the voice agent to the room
        # ---------------------------------------------------------

        logger.info(
            "Creating agent dispatch for agent 'my-agent' "
            "in room '%s'...",
            room_name,
        )

        dispatch_metadata = {
            "call_type": call_type,
            "user_name": user_name,
            "reminder": reminder,
        }

        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="my-agent",
                room=room_name,
                metadata=json.dumps(dispatch_metadata),
            )
        )

        logger.info("Agent dispatch created successfully.")

        # ---------------------------------------------------------
        # 2. Create the outbound SIP participant
        # ---------------------------------------------------------

        logger.info(
            "Dialing SIP participant to %s using trunk %s...",
            sip_call_to,
            sip_trunk_id,
        )

        participant_info = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=sip_call_to,
                room_name=room_name,
                participant_identity=f"sip_{sip_call_to}",
                participant_name=user_name or "SIP Callee",
                wait_until_answered=True,
            )
        )

        logger.info(
            "SIP call connected successfully. "
            "Participant SID: %s",
            participant_info.participant_sid,
        )

        return True, ""

    except Exception as e:
        logger.exception("Outbound SIP call failed")
        return False, str(e)

    finally:
        await lkapi.aclose()


async def handle_call(request):
    """
    HTTP POST /call

    Expected JSON:
    {
        "destination": "sip:abhishek2026@sip.linphone.org",
        "user_name": "Abhishek",
        "call_type": "medication_reminder",
        "reminder": "Your medication reminder"
    }
    """

    try:
        data = await request.json()
    except Exception:
        data = {}

    destination = (
        data.get("destination")
        or os.getenv("LINPHONE_SIP_URI")
    )

    user_name = data.get("user_name", "")
    call_type = data.get(
        "call_type",
        "medication_reminder",
    )
    reminder = data.get(
        "reminder",
        "Medication reminder",
    )

    # Check destination
    if not destination:
        err_msg = (
            "Missing destination SIP URI/phone number "
            "and LINPHONE_SIP_URI is not set."
        )

        logger.error(err_msg)

        return web.json_response(
            {"error": err_msg},
            status=400,
        )

    # Create unique room
    room_name = (
        f"outbound_room_"
        f"{int(time.time())}_"
        f"{os.urandom(2).hex()}"
    )

    logger.info(
        "Triggering outbound call server side to %s "
        "in room %s",
        destination,
        room_name,
    )

    # Trigger outbound call
    success, err_msg = await make_outbound_call(
        destination=destination,
        room_name=room_name,
        user_name=user_name,
        call_type=call_type,
        reminder=reminder,
    )

    if success:
        return web.json_response(
            {
                "success": True,
                "message": "Call connected successfully.",
                "room_name": room_name,
            }
        )

    return web.json_response(
        {
            "success": False,
            "error": err_msg or "Outbound call failed.",
            "room_name": room_name,
        },
        status=500,
    )


def start_trigger_server(port=5001):
    """
    Start the local HTTP server used by the frontend
    to trigger outbound calls.
    """

    app = web.Application()

    app.router.add_post(
        "/call",
        handle_call,
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s - "
            "%(name)s - "
            "%(levelname)s - "
            "%(message)s"
        ),
    )

    logger.info(
        "Starting backend trigger server on port %s...",
        port,
    )

    web.run_app(
        app,
        host="127.0.0.1",
        port=port,
        handle_signals=False,
    )


if __name__ == "__main__":
    load_dotenv(".env.local")

    import sys

    # ---------------------------------------------------------
    # CLI mode
    #
    # Example:
    # uv run python src/outbound_call.py \
    # sip:abhishek2026@sip.linphone.org
    # ---------------------------------------------------------

    if len(sys.argv) > 1 and sys.argv[1] != "--server":

        destination = sys.argv[1]

        room_name = (
            f"outbound_room_{int(time.time())}"
        )

        print(
            f"Dialing {destination} "
            f"in room {room_name}..."
        )

        logging.basicConfig(
            level=logging.INFO,
            format=(
                "%(asctime)s - "
                "%(name)s - "
                "%(levelname)s - "
                "%(message)s"
            ),
        )

        success, error = asyncio.run(
            make_outbound_call(
                destination=destination,
                room_name=room_name,
            )
        )

        if success:
            print(
                "Call completed/connected successfully."
            )
        else:
            print(
                f"Call failed: {error}"
            )

    else:
        # -----------------------------------------------------
        # Server mode
        # -----------------------------------------------------

        start_trigger_server(5001)
