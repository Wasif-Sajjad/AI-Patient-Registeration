"""
Voice agent webhook — Vapi implementation.

Vapi calls this endpoint as a "Server URL" tool during the conversation.
Each call carries a `message.toolCalls[]` array. We execute the first tool
call and return a `results` array that Vapi maps back to the correct call ID.

Tool names that Vapi must be configured with (in the dashboard):
  - find_patient_by_phone(phone_number)
  - register_patient(first_name, last_name, date_of_birth, sex, phone_number,
                     address_line_1, city, state, zip_code, ...optional)
  - update_patient(patient_id, ...fields to change)

Both REST API and this webhook share the same service layer — no duplicated
validation or business logic.
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.patient import PatientCreate, PatientOut, PatientUpdate
from app.services import patient_service
from app.services.patient_service import NotFoundError

router = APIRouter(prefix="/voice", tags=["voice"])
logger = logging.getLogger("voice")


def _verify_secret(x_webhook_secret: Optional[str]) -> None:
    if settings.voice_webhook_secret and x_webhook_secret != settings.voice_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid webhook secret")


def _extract_call(payload: dict) -> tuple[str, dict, str]:
    """
    Parse Vapi's Server URL webhook payload.

    Vapi sends:
    {
      "message": {
        "type": "tool-calls",
        "toolCalls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "register_patient",
              "arguments": { "first_name": "Jane", ... }
            }
          }
        ]
      }
    }

    Returns (function_name, arguments_dict, tool_call_id).
    """
    message = payload.get("message", {})

    # Vapi primary shape: message.toolCalls[]
    tool_calls = message.get("toolCalls") or []
    if tool_calls:
        call = tool_calls[0]
        tool_call_id = call.get("id", "")
        fn = call.get("function", {})
        name = fn.get("name", "")
        args = fn.get("arguments", {})
        # arguments may arrive as a JSON string in some Vapi versions
        if isinstance(args, str):
            args = json.loads(args)
        return name, args, tool_call_id

    # Fallback: some Vapi versions send toolWithToolCallList
    tool_with_list = message.get("toolWithToolCallList") or []
    if tool_with_list:
        item = tool_with_list[0]
        tc = item.get("toolCall", {})
        tool_call_id = tc.get("id", "")
        fn = tc.get("function", {})
        name = fn.get("name", "")
        args = fn.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        return name, args, tool_call_id

    # Retell-style fallback: {"name": "...", "args": {...}}
    if "name" in payload and "args" in payload:
        return payload["name"], payload["args"], ""

    # If it's a status update or other non-tool-call Vapi message, just ignore it gracefully
    msg_type = message.get("type", "")
    if msg_type in ["status-update", "end-of-call-report", "conversation-update", "transcript"]:
        return None, {}, ""

    raise HTTPException(status_code=422, detail=f"unrecognized tool-call payload shape: {msg_type}")


async def _dispatch(db: AsyncSession, function_name: str, args: dict) -> Any:
    if function_name is None:
        return {"ignored": True}
    if function_name == "find_patient_by_phone":
        patient = await patient_service.find_by_phone(db, args["phone_number"])
        if patient is None:
            return {"found": False}
        return {"found": True, "patient": PatientOut.model_validate(patient).model_dump(mode="json")}

    if function_name == "register_patient":
        try:
            payload = PatientCreate(**args)
        except ValidationError as e:
            # Surface field-level errors so the agent can re-prompt for that
            # specific field instead of failing the whole call.
            return {"success": False, "errors": e.errors()}
        patient = await patient_service.create_patient(db, payload)
        return {"success": True, "patient": PatientOut.model_validate(patient).model_dump(mode="json")}

    if function_name == "update_patient":
        patient_id = args.pop("patient_id")
        try:
            payload = PatientUpdate(**args)
        except ValidationError as e:
            return {"success": False, "errors": e.errors()}
        try:
            patient = await patient_service.update_patient(db, patient_id, payload)
        except NotFoundError:
            return {"success": False, "errors": [{"msg": "patient not found"}]}
        return {"success": True, "patient": PatientOut.model_validate(patient).model_dump(mode="json")}

    raise HTTPException(status_code=422, detail=f"unknown function '{function_name}'")


@router.post("/tool-call")
async def voice_tool_call(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(default=None),
):
    _verify_secret(x_webhook_secret)
    payload = await request.json()

    logger.info("Vapi webhook received: %s", json.dumps(payload, indent=2, default=str))

    function_name, args, tool_call_id = _extract_call(payload)
    result = await _dispatch(db, function_name, args)

    logger.info("Dispatched '%s' → result: %s", function_name, result)

    # Vapi expects a `results` array where each item maps toolCallId → result
    # https://docs.vapi.ai/server-url/setting-up-server-urls#tool-call-messages
    return {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": result,
            }
        ]
    }
