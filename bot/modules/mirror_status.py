from threading import Thread
from time import time
from random import choice
from psutil import (boot_time, cpu_count, cpu_percent, disk_usage,
                    net_io_counters, swap_memory, virtual_memory)
from telegram.ext import CallbackQueryHandler, CommandHandler

from bot import (DOWNLOAD_DIR, Interval, botStartTime, config_dict, dispatcher,
                 download_dict, download_dict_lock, status_reply_dict_lock)
from bot.helper.ext_utils.bot_utils import (get_readable_file_size,
                                            get_readable_time, new_thread,
                                            setInterval, turn)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (sendMessage, deleteMessage, auto_delete_message, sendStatusMessage, update_all_messages, delete_all_messages, editMessage, editCaption, sendPhoto)
from bot.__main__ import progress_bar

def mirror_status(update, context):
    with download_dict_lock:
        count = len(download_dict)
    if count == 0:
        currentTime = get_readable_time(time() - botStartTime)
        free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)
        cpuUsage = cpu_percent(interval=0.5)
        mem_p = memory.percent
        message = '⚠️No Active Downloads !\n\n '
        message += f'<b>CPU:</b> [{progress_bar(cpuUsage)}] {cpuUsage}%''\n 
                   f'<b>FREE</b>: {free}" || <b>UPTIME</b>: {currentTime}'' \n
                   f"<b>RAM:</b> [{progress_bar(mem_p)}] {mem_p}% "
        reply_message = sendPhoto(message, context.bot, update.message, choice(config_dict['PICS']))
        Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()
    else:
        sendStatusMessage(update.message, context.bot)
        deleteMessage(context.bot, update.message)
        with status_reply_dict_lock:
            if Interval:
                Interval[0].cancel()
                Interval.clear()
                Interval.append(setInterval(config_dict['DOWNLOAD_STATUS_UPDATE_INTERVAL'], update_all_messages))

@new_thread
def status_pages(update, context):
    query = update.callback_query
    msg = query.message
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    chat_id = update.effective_chat.id
    admins = context.bot.get_chat_member(chat_id, user_id).status in ['creator', 'administrator'] or user_id in [OWNER_ID]
    data = query.data
    data = data.split()
    if data[1] == "refresh":
        if config_dict['PICS']: editCaption(f"{user_name}, Refreshing Status...", msg)
        else: editMessage(f"{user_name}, Refreshing Status...", msg)
        sleep(2)
        update_all_messages()
        query.answer()
    if data[1] == "stats":
        stats = pop_up_stats()
        query.answer(text=stats, show_alert=True)
    if data[1] == "close":
        if admins:
            delete_all_messages()
            query.answer()
        else:
            query.answer(text=f"{user_name}, You Don't Have Rights To Close This!", show_alert=True)
    if data[1] == "pre" or "nex":
        done = turn(data)
    if done:
        update_all_messages(True)
        query.answer()
    else:
        msg.delete()


mirror_status_handler = CommandHandler(BotCommands.StatusCommand, mirror_status,
                                      filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
status_pages_handler = CallbackQueryHandler(status_pages, pattern="status")

dispatcher.add_handler(mirror_status_handler)
dispatcher.add_handler(status_pages_handler)