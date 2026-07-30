from telethon.tl.types import Channel
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.channel import TelegramChannel
    from app.core.logging import get_logger
    import uuid

    logger = get_logger(__name__)


    async def discover_and_register_channels(userbot_manager, account_id: str) -> dict:
      """
      Only finds channels where the account is creator or admin with post rights.
      - Not in DB -> add it (active=True)
      - In DB but inactive -> reactivate
      - DB channels no longer admin -> deactivate
        SAFETY: if iter_dialogs returns 0 results, skip deactivation entirely
                (likely a transient network/session error, not a real change).
      """
      client_wrapper = userbot_manager.get_client(account_id)
      if not client_wrapper or not client_wrapper.is_connected:
          return {"error": "account_not_connected", "found": 0, "added": 0, "reactivated": 0, "channels": []}

      client = client_wrapper.client

      admin_channels = []

      try:
          async for dialog in client.iter_dialogs():
              entity = dialog.entity

              if not isinstance(entity, Channel):
                  continue
              if not getattr(entity, "broadcast", False):
                  continue

              is_creator = getattr(entity, "creator", False)
              admin_rights = getattr(entity, "admin_rights", None)

              if not is_creator and not admin_rights:
                  continue

              if admin_rights and not is_creator:
                  can_post = getattr(admin_rights, "post_messages", False)
                  if not can_post:
                      continue

              tg_id = int(f"-100{entity.id}") if entity.id > 0 else entity.id

              admin_channels.append({
                  "telegram_id": tg_id,
                  "username": getattr(entity, "username", None),
                  "title": getattr(entity, "title", None),
                  "is_creator": is_creator,
              })
              logger.info("admin_channel_found", title=entity.title, creator=is_creator)

      except Exception as e:
          logger.error("dialog_scan_failed", error=str(e))
          return {"error": str(e), "found": 0, "added": 0, "reactivated": 0, "channels": []}

      # --- Safety guard ---------------------------------------------------
      # If iter_dialogs returned 0 admin channels, do NOT deactivate existing
      # records. This protects against transient network/session errors that
      # return an empty dialog list wiping all channels and killing auto-posting.
      if not admin_channels:
          logger.warning(
              "scan_returned_zero_channels_skipping_deactivation",
              account_id=account_id,
              note="iter_dialogs returned 0 admin channels -- skipping deactivation of existing records",
          )
          return {"found": 0, "added": 0, "reactivated": 0, "channels": []}

      added = 0
      reactivated = 0
      admin_tg_ids = {ch["telegram_id"] for ch in admin_channels}

      async with AsyncSessionLocal() as session:
          account_uuid = uuid.UUID(account_id)

          existing_result = await session.execute(
              select(TelegramChannel).where(TelegramChannel.account_id == account_uuid)
          )
          existing_records = {r.telegram_channel_id: r for r in existing_result.scalars().all()}

          for ch in admin_channels:
              tg_id = ch["telegram_id"]

              if tg_id in existing_records:
                  record = existing_records[tg_id]
                  if not record.is_active:
                      record.is_active = True
                      reactivated += 1
                      logger.info("channel_reactivated", title=ch["title"])
              else:
                  channel = TelegramChannel(
                      account_id=account_uuid,
                      telegram_channel_id=tg_id,
                      username=ch["username"],
                      display_name=ch["title"],
                      language="en",
                      is_active=True,
                  )
                  session.add(channel)
                  added += 1
                  logger.info("channel_registered", title=ch["title"])

          # Deactivate channels we are no longer admin of
          # (only reached when scan returned at least one result -- see guard above)
          for tg_id, record in existing_records.items():
              if tg_id not in admin_tg_ids and record.is_active:
                  record.is_active = False
                  logger.info("channel_deactivated_not_admin", title=record.display_name)

          await session.commit()

      logger.info("scan_complete", found=len(admin_channels), added=added, reactivated=reactivated)
      return {
          "found": len(admin_channels),
          "added": added,
          "reactivated": reactivated,
          "channels": [
              {"title": c["title"], "username": c["username"], "is_creator": c["is_creator"]}
              for c in admin_channels
          ],
      }
    