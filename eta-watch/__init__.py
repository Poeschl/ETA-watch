import logging
from functools import wraps
from typing import Optional, Union

import pyeta
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.ext._utils.types import FilterDataDict
from telegram.ext.filters import MessageFilter

from config import read_config, save_ref_settings


def send_typing_action(func):
  """Sends typing action while processing func command."""

  @wraps(func)
  async def command_func(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    return await func(self, update, context, *args, **kwargs)

  return command_func


class UserFilter(MessageFilter):

  def __init__(self):
    self.config = read_config()

  def filter(self, message: Message) -> Optional[Union[bool, FilterDataDict]]:
    return message.chat_id in self.config["users"]


userFilter = UserFilter()


class EtaWatcherBot:

  def __init__(self, config: dict):
    if len(config["users"]) == 0 or config["bot_token"] == "":
      logging.error("You need to insert at least one allowed user id and your telegram bot token.")
      exit(1)

    if config["eta_host"] == "":
      logging.error("You need to insert your host address of your ETA heating system.")
      exit(1)

    logging.info("Starting ETA-watch bot")
    self.eta = pyeta.Eta(config["eta_host"])

  def get_eta_settings(self) -> dict:
    nodes = self.eta.get_nodes()

    for section in nodes:
      logging.info(f"Retrieve data for {section}")
      self.eta.update_eta_object(nodes[section])

    return nodes

  def save_ref_setting(self):
    save_ref_settings(self.get_eta_settings())

  def run(self):
    config = read_config()
    if config["reference_settings"] == {}:
      logging.info("Retrieve first full reference setting. (May take some time)")
      self.save_ref_setting()

    bot_application = ApplicationBuilder().token(config["bot_token"]).build()
    bot_application.add_handler(CommandHandler("start", self.start, userFilter))
    bot_application.run_polling()

  @send_typing_action
  async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
      text="Started the ETA-watch bot!"
    )

    keyboard = [
      [
        InlineKeyboardButton("Edit reference settings", callback_data="edit"),
      ],
      [
        InlineKeyboardButton("Retrieve new reference settings. ⚠ Will overwrite existing", callback_data="retrieve"),
      ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Available actions:", reply_markup=reply_markup)

  @send_typing_action
  async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "edit":
      reference_settings = read_config()["reference_settings"]
      await update.message.reply_markdown(f"The current reference config:\n```{reference_settings}```")
    elif query.data == "retrieve":
      pass


if __name__ == '__main__':
  logging.basicConfig(level="INFO")
  logging.getLogger("httpx").setLevel("WARN")

  EtaWatcherBot(read_config()).run()
