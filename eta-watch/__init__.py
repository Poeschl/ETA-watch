import logging
import os
import re
import traceback
from enum import auto, StrEnum
from tempfile import TemporaryFile
from typing import Optional, Union

import pyeta
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from telegram.ext._utils.types import FilterDataDict
from telegram.ext.filters import MessageFilter

from config import read_config, save_ref_settings, load_yaml_ref_settings, save_yaml_ref_settings


class UserFilter(MessageFilter):

  def __init__(self):
    super().__init__()
    self.config = read_config()

  def filter(self, message: Message) -> Optional[Union[bool, FilterDataDict]]:
    return message.chat_id in self.config["users"]


userFilter = UserFilter()


class STATES(StrEnum):
  MAIN = auto()
  EDIT = auto()
  RESET = auto()


class CALLBACK(StrEnum):
  MAIN_CHECK = auto()
  MAIN_EDIT = auto()
  MAIN_RESET = auto()
  RESET_YES = auto()
  RESET_NO = auto()


async def send_typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)


async def send_upload_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> STATES:
  """Sends the main option menu"""
  keyboard = [
    [InlineKeyboardButton("Check against reference", callback_data=CALLBACK.MAIN_CHECK)],
    [InlineKeyboardButton("Edit current reference", callback_data=CALLBACK.MAIN_EDIT)],
    [InlineKeyboardButton("Reset current reference", callback_data=CALLBACK.MAIN_RESET)]
  ]

  reply_markup = InlineKeyboardMarkup(keyboard)
  await context.bot.send_message(chat_id=update.effective_message.chat_id, text="Possible actions:", reply_markup=reply_markup)
  return STATES.MAIN


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> STATES:
  query = update.callback_query
  await query.answer()

  if query.data == CALLBACK.MAIN_CHECK:
    logging.info("Checking against reference")
    # TBD
    await query.message.reply_text("Not implemented yet")
    return STATES.MAIN

  elif query.data == CALLBACK.MAIN_EDIT:
    logging.info("Edit")
    return await edit_menu(update, context)

  elif query.data == CALLBACK.MAIN_RESET:
    return await reset_menu(update, context)


async def edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> STATES:
  await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                 text="Current reference will be uploaded as file. Send back your reference with the keys you want to be the new reference.")
  await send_upload_action(update, context)

  with TemporaryFile(mode="w+", encoding="UTF-8", prefix="ETA-ref-", suffix=".yaml") as temp_file:
    temp_file.writelines(load_yaml_ref_settings())
    temp_file.flush()
    temp_file.seek(0)
    logging.info("Wrote ref file %s", temp_file.name)

    await send_upload_action(update, context)
    await context.bot.send_document(chat_id=update.effective_message.chat_id, document=temp_file)

  return STATES.EDIT


async def handle_edit_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> STATES:
  remote_file = await context.bot.get_file(update.message.document)
  local_file = await remote_file.download_to_drive()

  with open(local_file, "r") as reader:
    try:
      save_yaml_ref_settings(reader.read())
    except TypeError:
      await update.message.reply_text("The uploaded file contains an error. Please correct it and try again.")
      await update.message.reply_text(traceback.format_exc())
      return STATES.EDIT
  os.remove(local_file)

  logging.info("New reference is saved")
  await update.message.reply_text("New reference is saved!")
  return await main_menu(update, context)


async def reset_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> STATES:
  """Sends the main option menu"""
  keyboard = [
    [InlineKeyboardButton("Yes, reset whole reference", callback_data=CALLBACK.RESET_YES)],
    [InlineKeyboardButton("No, abort, abort!!", callback_data=CALLBACK.RESET_NO)]
  ]

  reply_markup = InlineKeyboardMarkup(keyboard)

  await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                 text="Are you sure to remove the current reference and reset it with the full config of your ETA system?",
                                 reply_markup=reply_markup)
  return STATES.RESET


async def handle_reset_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> STATES:
  query = update.callback_query
  await query.answer()

  if query.data == CALLBACK.RESET_YES:
    logging.info("Reset eta reference")
    await query.message.reply_text("Reset reference settings... (Will take some time)")
    await send_typing_action(update, context)
    save_ref_settings(reset_eta_settings())
    await query.message.reply_text("Reset reference settings!")

  return await main_menu(update, context)


def reset_eta_settings() -> dict:
  nodes = eta.get_nodes()

  for section in nodes:
    logging.info(f"Retrieve data for {section}")
    eta.update_eta_object(nodes[section])

  return nodes


if __name__ == '__main__':
  logging.basicConfig(level="INFO")
  logging.getLogger("httpx").setLevel("WARN")

  config = read_config()

  if len(config["users"]) == 0 or config["bot_token"] == "":
    logging.error("You need to insert at least one allowed user id and your telegram bot token.")
    exit(1)

  if config["eta_host"] == "":
    logging.error("You need to insert your host address of your ETA heating system.")
    exit(1)

  logging.info("Starting ETA-watch bot")
  eta = pyeta.Eta(config["eta_host"])

  config = read_config()

  if config["reference_settings"] == {}:
    logging.info("Retrieve first full reference setting. (May take some time)")
    save_ref_settings(reset_eta_settings())

  bot_application = ApplicationBuilder().token(config["bot_token"]).build()

  conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", main_menu)],
    states={
      STATES.MAIN: [
        CallbackQueryHandler(callback=handle_main_menu, pattern=re.compile("main_.*"))
      ],
      STATES.EDIT: [
        MessageHandler(filters=filters.Document.ALL, callback=handle_edit_upload)
      ],
      STATES.RESET: [
        CallbackQueryHandler(callback=handle_reset_menu, pattern=re.compile("reset_.*"))
      ]
    },
    fallbacks=[CommandHandler(["start", "cancel"], main_menu)]
  )

  bot_application.add_handler(conversation_handler)
  bot_application.run_polling()
