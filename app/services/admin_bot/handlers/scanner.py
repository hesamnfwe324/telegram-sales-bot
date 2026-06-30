import asyncio
  from aiogram import Router, F
  from aiogram.types import Message, CallbackQuery
  from aiogram.filters import Command
  from aiogram.fsm.context import FSMContext
  from aiogram.fsm.state import State, StatesGroup
  from aiogram.utils.keyboard import InlineKeyboardBuilder
  from app.services.admin_bot.keyboards import back_kb
  from app.core.logging import get_logger

  logger = get_logger(__name__)
  router = Router()

  MAX_IPS = 8_000
  PORT = 3389

  COUNTRIES = {
      "us": "🇺🇸 USA",
      "de": "🇩🇪 Germany",
      "nl": "🇳🇱 Netherlands",
      "fr": "🇫🇷 France",
      "gb": "🇬🇧 UK",
      "ru": "🇷🇺 Russia",
      "tr": "🇹🇷 Turkey",
      "br": "🇧🇷 Brazil",
      "ir": "🇮🇷 Iran",
      "cn": "🇨🇳 China",
      "ca": "🇨🇦 Canada",
      "au": "🇦🇺 Australia",
  }


  class ScanState(StatesGroup):
      waiting_country = State()


  def country_kb():
      builder = InlineKeyboardBuilder()
      for code, name in COUNTRIES.items():
          builder.button(text=name, callback_data=f"scan_cc:{code}")
      builder.button(text="✏️ Custom code", callback_data="scan_custom")
      builder.button(text="🔙 Back", callback_data="main_menu")
      builder.adjust(2)
      return builder.as_markup()


  @router.message(Command("scan"))
  @router.callback_query(F.data == "scanner")
  async def cmd_scan(event: Message | CallbackQuery, state: FSMContext):
      await state.clear()
      msg = event if isinstance(event, Message) else event.message
      await msg.answer(
          "🔍 *IP Scanner — RDP Finder*\n\n"
          f"Scans IPs in a country for open port *{PORT} (RDP)*.\n"
          "Select a country:",
          parse_mode="Markdown",
          reply_markup=country_kb(),
      )
      if isinstance(event, CallbackQuery):
          await event.answer()


  @router.callback_query(F.data.startswith("scan_cc:"))
  async def on_country_cb(callback: CallbackQuery, state: FSMContext):
      cc = callback.data.split(":")[1]
      name = COUNTRIES.get(cc, cc.upper())
      await callback.message.edit_text(
          f"⏳ Fetching IP ranges for *{name}* ...",
          parse_mode="Markdown",
      )
      await callback.answer()
      await _run_scan(callback.message, cc)


  @router.callback_query(F.data == "scan_custom")
  async def on_custom_cb(callback: CallbackQuery, state: FSMContext):
      await state.set_state(ScanState.waiting_country)
      await callback.message.answer(
          "🌍 Send the 2-letter country code (e.g. `US`, `DE`, `NL`):",
          parse_mode="Markdown",
      )
      await callback.answer()


  @router.message(ScanState.waiting_country)
  async def on_country_input(message: Message, state: FSMContext):
      cc = message.text.strip().lower()
      if len(cc) != 2 or not cc.isalpha():
          await message.answer("❌ Must be exactly 2 letters. Try again:")
          return
      await state.clear()
      status_msg = await message.answer(
          f"⏳ Fetching IP ranges for *{cc.upper()}* ...", parse_mode="Markdown"
      )
      await _run_scan(status_msg, cc)


  async def _run_scan(msg: Message, cc: str):
      from app.services.scanner.ip_ranges import get_country_cidr_blocks
      from app.services.scanner.port_scanner import scan_port

      try:
          cidrs = await get_country_cidr_blocks(cc)
      except ValueError as e:
          await msg.answer(f"❌ {e}", parse_mode="Markdown")
          return
      except Exception as e:
          await msg.answer(f"❌ Failed to fetch ranges: `{e}`", parse_mode="Markdown")
          return

      if not cidrs:
          await msg.answer(f"❌ No IP ranges for `{cc.upper()}`.")
          return

      await msg.answer(
          f"📡 *Scan started*\n"
          f"Country: `{cc.upper()}`  |  CIDRs: `{len(cidrs)}`\n"
          f"Max IPs: `{MAX_IPS:,}`  |  Port: `{PORT} (RDP)`\n\n"
          f"⏳ This may take 1–3 minutes ...",
          parse_mode="Markdown",
      )

      logger.info("rdp_scan_started", country=cc.upper(), cidrs=len(cidrs))

      try:
          found = await scan_port(cidrs, port=PORT, max_ips=MAX_IPS, timeout=1.2)
      except Exception as e:
          logger.error("rdp_scan_error", error=str(e))
          await msg.answer(f"❌ Scan error: `{e}`", parse_mode="Markdown")
          return

      logger.info("rdp_scan_done", country=cc.upper(), found=len(found))

      if not found:
          await msg.answer(
              f"✅ *Scan done.* No open RDP ports found in {MAX_IPS:,} sampled IPs.",
              parse_mode="Markdown",
              reply_markup=back_kb(),
          )
          return

      chunk_size = 25
      for i in range(0, len(found), chunk_size):
          chunk = found[i : i + chunk_size]
          lines = "\n".join(f"`{ip}:{PORT}`" for ip in chunk)
          header = "🟢 *Open RDP found:*\n" if i == 0 else "🟢 *(cont.)*\n"
          await msg.answer(header + lines, parse_mode="Markdown")
          await asyncio.sleep(0.3)

      await msg.answer(
          f"✅ *Scan complete!*\n"
          f"Found `{len(found)}` IPs with RDP open (from {MAX_IPS:,} sampled).",
          parse_mode="Markdown",
          reply_markup=back_kb(),
      )
  