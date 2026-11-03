from fastapi import APIRouter
from fastapi.responses import JSONResponse

from model.ConversationDTO import ConversationDTO, ConversationTitleDTO
from services import conversationsService, databaseService

router = APIRouter(prefix="/conversations")


def _not_found(conversation_id):
    return JSONResponse(content={"status": "error", "message": f"Conversation {conversation_id} not found"},
                        status_code=404)


def _invalid(e):
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)


@router.get("")
def listConversations():
    return conversationsService.list_conversations()


@router.get("/{conversation_id}")
def getConversation(conversation_id: str):
    try:
        conversation = conversationsService.get_conversation(conversation_id)
    except ValueError as e:
        return _invalid(e)
    return conversation if conversation is not None else _not_found(conversation_id)


@router.put("/{conversation_id}")
def saveConversation(conversation_id: str, conversation: ConversationDTO):
    try:
        saved = conversationsService.save_conversation(
            conversation_id, conversation.title, conversation.messages,
            conversation.database or databaseService.get_current_database_name())
    except ValueError as e:
        return _invalid(e)
    return {k: v for k, v in saved.items() if k != "messages"}


@router.patch("/{conversation_id}")
def renameConversation(conversation_id: str, request: ConversationTitleDTO):
    try:
        conversation = conversationsService.rename_conversation(conversation_id, request.title.strip())
    except ValueError as e:
        return _invalid(e)
    if conversation is None:
        return _not_found(conversation_id)
    return {k: v for k, v in conversation.items() if k != "messages"}


@router.delete("/{conversation_id}")
def deleteConversation(conversation_id: str):
    try:
        deleted = conversationsService.delete_conversation(conversation_id)
    except ValueError as e:
        return _invalid(e)
    return {"status": "ok"} if deleted else _not_found(conversation_id)
