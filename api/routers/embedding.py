from fastapi import APIRouter, HTTPException
from loguru import logger

from api.command_service import CommandService
from api.models import EmbedRequest, EmbedResponse
from open_notebook.ai.models import model_manager
from open_notebook.domain.notebook import Note, Source

router = APIRouter()


@router.post("/embed", response_model=EmbedResponse)
async def embed_content(embed_request: EmbedRequest):
    """Embed content for vector search."""
    try:
        # Check if embedding model is available
        if not await model_manager.get_embedding_model():
            raise HTTPException(
                status_code=400,
                detail="No embedding model configured. Please configure one in the Models section.",
            )

        item_id = embed_request.item_id
        item_type = embed_request.item_type.lower()

        # Validate item type
        if item_type not in ["source", "note"]:
            raise HTTPException(
                status_code=400, detail="Item type must be either 'source' or 'note'"
            )

        # Branch based on processing mode
        if embed_request.async_processing:
            # ASYNC PATH: Submit command for background processing
            logger.info(f"Using async processing for {item_type} {item_id}")

            try:
                # Import commands to ensure they're registered
                import commands.embedding_commands  # noqa: F401

                # Submit type-specific command
                if item_type == "source":
                    command_name = "embed_source"
                    command_input = {"source_id": item_id}
                else:  # note
                    command_name = "embed_note"
                    command_input = {"note_id": item_id}

                command_id = await CommandService.submit_command_job(
                    "open_notebook",
                    command_name,
                    command_input,
                )

                logger.info(f"Submitted async {command_name} command: {command_id}")

                return EmbedResponse(
                    success=True,
                    message="Embedding queued for background processing",
                    item_id=item_id,
                    item_type=item_type,
                    command_id=command_id,
                )

            except Exception as e:
                logger.error(f"Failed to submit async embedding command: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to queue embedding: {str(e)}"
                )

        else:
            # DOMAIN MODEL PATH: Submit job via domain model convenience methods
            # These methods internally call submit_command() - still fire-and-forget
            logger.info(f"Using domain model path for {item_type} {item_id}")

            command_id = None

            # Get the item and submit embedding job
            if item_type == "source":
                source_item = await Source.get(item_id)
                if not source_item:
                    raise HTTPException(status_code=404, detail="Source not found")

                # Check if source has content before attempting to vectorize
                if not source_item.full_text or not source_item.full_text.strip():
                    error_detail = f"Source {item_id} cannot be embedded because it contains no text content"
                    if source_item.full_text is None:
                        error_detail += " (full_text field is None)"
                    elif not source_item.full_text.strip():
                        error_detail += (
                            " (full_text field is empty or contains only whitespace)"
                        )

                    # Check if source is still processing
                    if source_item.command:
                        try:
                            status = await source_item.get_status()
                            if status in ["queued", "running"]:
                                error_detail += ". Source is still being processed, please wait for completion."
                            elif status == "failed":
                                error_detail += ". Source processing failed, try retrying the source processing."
                            elif status == "completed":
                                error_detail += ". Source processing completed but no text was extracted."
                        except Exception:
                            pass

                    logger.warning(error_detail)
                    raise HTTPException(status_code=400, detail=error_detail)

                # Submit embed_source job (returns command_id for tracking)
                command_id = await source_item.vectorize()
                message = "Source embedding job submitted"

            elif item_type == "note":
                note_item = await Note.get(item_id)
                if not note_item:
                    raise HTTPException(status_code=404, detail="Note not found")

                # Check if note has content before attempting to embed
                if not note_item.content or not note_item.content.strip():
                    error_detail = f"Note {item_id} cannot be embedded because it contains no text content"
                    if note_item.content is None:
                        error_detail += " (content field is None)"
                    elif not note_item.content.strip():
                        error_detail += (
                            " (content field is empty or contains only whitespace)"
                        )

                    logger.warning(error_detail)
                    raise HTTPException(status_code=400, detail=error_detail)

                # Note.save() internally submits embed_note command and returns command_id
                command_id = await note_item.save()
                message = "Note embedding job submitted"

            return EmbedResponse(
                success=True,
                message=message,
                item_id=item_id,
                item_type=item_type,
                command_id=command_id,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error embedding {embed_request.item_type} {embed_request.item_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error embedding content: {str(e)}"
        )
