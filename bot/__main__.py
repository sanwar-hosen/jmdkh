from os import execl, path, remove
from signal import SIGINT, signal
from bs4 import BeautifulSoup
from requests import get as rget
from subprocess import check_output, run
from sys import executable
from time import time
from datetime import datetime
from pytz import timezone
from random import choice
from psutil import (boot_time, cpu_count, cpu_percent, disk_usage,
                    net_io_counters, swap_memory, virtual_memory)
from telegram.ext import CommandHandler
from telegram import ChatPermissions, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from .helper.telegram_helper.button_build import ButtonMaker
from .helper.ext_utils.telegraph_helper import telegraph
from bot import (DATABASE_URL, IGNORE_PENDING_REQUESTS,
                 INCOMPLETE_TASK_NOTIFIER, LOGGER, STOP_DUPLICATE_TASKS,
                 TORRENT_LIMIT, USER_MAX_TASKS, DIRECT_LIMIT, LEECH_LIMIT, CLONE_LIMIT, MEGA_LIMIT, YTDLP_LIMIT,
                 Interval, QbInterval, app, bot, botStartTime, config_dict,
                 dispatcher, main_loop, updater)
from bot.helper.ext_utils.bot_utils import (get_readable_file_size,
                                            get_readable_time, set_commands)
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.fs_utils import (clean_all, exit_clean_up,
                                           start_cleanup)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (editMessage, sendLogFile, sendMessage, sendPhoto, editPhoto, sendMarkup)
from bot.modules import (authorize, bot_settings, bt_select, cancel_mirror,
                         category_select, count, delete, drive_list,
                         eval, mirror_leech, mirror_status, rmdb, rss,
                         save_message, search, shell, users_settings, ytdlp, anonymous)

timez = config_dict['TIMEZONE']
now=datetime.now(timezone(f'{timez}'))

def progress_bar(percentage):
    p_used = config_dict['FINISHED_PROGRESS_STR']
    p_total = config_dict['UN_FINISHED_PROGRESS_STR']
    if isinstance(percentage, str):
        return 'NaN'
    try:
        percentage=int(percentage)
    except:
        percentage = 0
    return ''.join(
        p_used if i <= percentage // 7 else p_total for i in range(1, 8)
    )

def stats(update, context):
    total, used, free, disk = disk_usage('/')
    swap = swap_memory()
    memory = virtual_memory()
    if path.exists('.git'):
        last_commit = check_output(["git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'"], shell=True).decode()
    else:
        last_commit = 'No UPSTREAM_REPO'
    currentTime = get_readable_time(time() - botStartTime)
    current = now.strftime('%m/%d %I:%M:%S %p')
    osUptime = get_readable_time(time() - boot_time())
    total, used, free, disk= disk_usage('/')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(net_io_counters().bytes_sent)
    recv = get_readable_file_size(net_io_counters().bytes_recv)
    cpuUsage = cpu_percent(interval=0.5)
    p_core = cpu_count(logical=False)
    t_core = cpu_count(logical=True)
    swap = swap_memory()
    swap_p = swap.percent
    swap_t = get_readable_file_size(swap.total)
    swap_u = get_readable_file_size(swap.used)
    memory = virtual_memory()
    mem_p = memory.percent
    mem_t = get_readable_file_size(memory.total)
    mem_a = get_readable_file_size(memory.available)
    mem_u = get_readable_file_size(memory.used)

    stats = f'<b>╭─《🌐 BOT STATISTICS 🌐》</b>\n' \
            f'<b>├  Updated On: </b>{last_commit}\n'\
            f'<b>├  Uptime: </b>{currentTime}\n'\
                    f'<b>├  OS Uptime: </b>{osUptime}\n'\
                    f'<b>├  CPU:</b> [{progress_bar(cpuUsage)}] {cpuUsage}%\n'\
             f'<b>├  RAM:</b> [{progress_bar(mem_p)}] {mem_p}%\n'\
             f'<b>├  Disk:</b> [{progress_bar(disk)}] {disk}%\n'\
                    f'<b>├  Disk Free:</b> {free}\n'\
            f'<b>├  Upload Data:</b> {sent}\n'\
            f'<b>╰  Download Data:</b> {recv}\n\n'\
            f'<b>╭─《 ⚠️ BOT LIMITS ⚠️ 》</b>\n'\
            f'<b>├  Torrent: </b>{TORRENT_LIMIT}GB/Link\n'\
            f'<b>├  Direct: </b>{DIRECT_LIMIT}GB/Link\n'\
            f'<b>├  Leech: </b>{LEECH_LIMIT}GB/Link\n'\
            f'<b>├  Clone: </b>{CLONE_LIMIT}GB/Link\n'\
            f'<b>├  Mega: </b>{MEGA_LIMIT}GB/Link\n'\
            f'<b>├  YT-limit: </b>{YTDLP_LIMIT}GB/Link\n'\
            f'<b>╰  User Tasks: </b>{USER_MAX_TASKS}Tasks/user'

    sendPhoto(stats, context.bot, update.message, choice(config_dict['PICS']))

def start(update, context):
    if config_dict['DM_MODE']:
        start_string = 'Bot Started.\n' \
                    'Now I will send your files or links here.\n'
    else:
        start_string = '🌹 Welcome To A heavily Modified Mirror Bot Of TheSano\n' \
                    'This bot can Mirror all your links To Google Drive!\n\n' \
                    '👨🏽‍💻 Powered By: @TheSano\n' \
                    ' Mother Repo: JMDKH-mltb'
    sendPhoto(start_string, context.bot, update.message, config_dict['START_PIC'])

def restart(update, context):
    restart_message = sendMessage("Restarting...", context.bot, update.message)
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    if QbInterval:
        QbInterval[0].cancel()
        QbInterval.clear()
    clean_all()
    run(["pkill", "-9", "-f", "gunicorn|aria2c|qbittorrent-nox|ffmpeg"])
    run(["python3", "update.py"])
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update.message)
    end_time = int(round(time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update.message)

help_string = '''
The Ultimate Telegram MIrror-Leech Bot to Upload Your File & Link in Google Drive & Telegram
Choose a help category:
'''
help_string_telegraph_user = f'''
<b><u>👤 User Commands</u></b>
<br><br>
• <b>/{BotCommands.HelpCommand}</b>: To get this message
<br><br>
• <b>/{BotCommands.MirrorCommand[0]}</b> [download_url][magnet_link]: Start mirroring to Google Drive. Send <b>/{BotCommands.MirrorCommand[0]}</b> for more help
<br><br>
• <b>/{BotCommands.ZipMirrorCommand[0]}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.UnzipMirrorCommand[0]}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.QbMirrorCommand[0]}</b> [magnet_link][torrent_file][torrent_file_url]: Start Mirroring using qBittorrent, Use <b>/{BotCommands.QbMirrorCommand[0]} s</b> to select files before downloading
<br><br>
• <b>/{BotCommands.QbZipMirrorCommand[0]}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.QbUnzipMirrorCommand[0]}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.LeechCommand[0]}</b> [download_url][magnet_link]: Start leeching to Telegram, Use <b>/{BotCommands.LeechCommand[0]} s</b> to select files before leeching
<br><br>
• <b>/{BotCommands.ZipLeechCommand[0]}</b> [download_url][magnet_link]: Start leeching to Telegram and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.UnzipLeechCommand[0]}</b> [download_url][magnet_link][torent_file]: Start leeching to Telegram and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.QbLeechCommand[0]}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent, Use <b>/{BotCommands.QbLeechCommand[0]} s</b> to select files before leeching
<br><br>
• <b>/{BotCommands.QbZipLeechCommand[0]}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.QbUnzipLeechCommand[0]}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.CloneCommand[0]}</b> [drive_url][gdtot_url]: Copy file/folder to Google Drive
<br><br>
• <b>/{BotCommands.CountCommand}</b> [drive_url][gdtot_url]: Count file/folder of Google Drive
<br><br>
• <b>/{BotCommands.DeleteCommand}</b> [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo)
<br><br>
• <b>/{BotCommands.YtdlCommand[0]}</b> [yt-dlp supported link]: Mirror yt-dlp supported link. Send <b>/{BotCommands.YtdlCommand[0]}</b> for more help
<br><br>
• <b>/{BotCommands.YtdlZipCommand[0]}</b> [yt-dlp supported link]: Mirror yt-dlp supported link as zip
<br><br>
• <b>/{BotCommands.YtdlLeechCommand[0]}</b> [yt-dlp supported link]: Leech yt-dlp supported link
<br><br>
• <b>/{BotCommands.YtdlZipLeechCommand[0]}</b> [yt-dlp supported link]: Leech yt-dlp supported link as zip
<br><br>
• <b>/{BotCommands.UserSetCommand[0]}</b>: Users settings
<br><br>
• <b>/{BotCommands.RssListCommand}</b>: List all subscribed rss feed info
<br><br>
• <b>/{BotCommands.RssGetCommand}</b>: [Title] [Number](last N links): Force fetch last N links
<br><br>
• <b>/{BotCommands.RssSubCommand}</b>: [Title] [Rss Link] f: [filter]: Subscribe new rss feed
<br><br>
• <b>/{BotCommands.RssUnSubCommand}</b>: [Title]: Unubscribe rss feed by title
<br><br>
• <b>/{BotCommands.RssSettingsCommand}</b>: Rss Settings
<br><br>
• <b>/{BotCommands.CancelMirror}</b>: Reply to the message by which the download was initiated and that download will be cancelled
<br><br>
• <b>/{BotCommands.CancelAllCommand}</b>: Cancel all downloading tasks
<br><br>
• <b>/{BotCommands.ListCommand}</b> [query]: Search in Google Drive(s)
<br><br>
• <b>/{BotCommands.SearchCommand}</b> [query]: Search for torrents with API
<br>sites: <code>rarbg, 1337x, yts, etzv, tgx, torlock, piratebay, nyaasi, ettv</code><br><br>
• <b>/{BotCommands.StatusCommand}</b>: Shows a status of all the downloads
<br><br>
• <b>/{BotCommands.StatsCommand}</b>: Show Stats of the machine the bot is hosted on
<br><br>
• <b>/{BotCommands.SpeedCommand[0]}</b>: Speedtest of server
<br><br>
'''

help_user = telegraph.create_page(
    title="Help",
    content=help_string_telegraph_user)["path"]

def bot_help(update, context):
    button = ButtonMaker()
    button.buildbutton("Help", f"https://telegra.ph/{help_user}")
    button.buildbutton(f"support chat", f"https://t.me/{config_dict['SUPPORT_CHAT']}")
    
    sendMessage(help_string, context.bot, update.message, button.build_menu(2))

def main():
    set_commands(bot)
    start_cleanup()

    if config_dict['WALLCRAFT_CATEGORY']:
        for page in range(1,20):
            r2 = rget(f"https://wallpaperscraft.com/catalog/{config_dict['WALLCRAFT_CATEGORY']}/1280x720/page{page}")
            soup2 = BeautifulSoup(r2.text, "html.parser")
            x = soup2.select('img[src^="https://images.wallpaperscraft.com/image/single"]')
            for img in x:
              config_dict['PICS'].append((img['src']).replace("300x168", "1280x720"))

    if DATABASE_URL and STOP_DUPLICATE_TASKS:
        DbManger().clear_download_links()
    if INCOMPLETE_TASK_NOTIFIER and DATABASE_URL:
        if notifier_dict:= DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                if path.isfile(".restartmsg"):
                    with open(".restartmsg") as f:
                        chat_id, msg_id = map(int, f)
                    msg = 'Restarted Successfully!'
                else:
                    msg = 'Bot Restarted!'
                for tag, links in data.items():
                    msg += f"\n\n{tag}: "
                    for index, link in enumerate(links, start=1):
                        msg += f" <a href='{link}'>{index}</a> |"
                        if len(msg.encode()) > 4000:
                            if 'Restarted Successfully!' in msg and cid == chat_id:
                                try:
                                    bot.editMessageText('Restarted Successfully!', chat_id, msg_id)
                                    bot.sendMessage(chat_id, msg, reply_to_message_id=msg_id)
                                except:
                                    pass
                                remove(".restartmsg")
                            else:
                                try:
                                    bot.sendMessage(cid, msg)
                                except Exception as e:
                                    LOGGER.error(e)
                            msg = ''
                if 'Restarted Successfully!' in msg and cid == chat_id:
                    try:
                        bot.editMessageText('Restarted Successfully!', chat_id, msg_id)
                        bot.sendMessage(chat_id, msg, reply_to_message_id=msg_id)
                    except:
                        pass
                    remove(".restartmsg")
                else:
                    try:
                        bot.sendMessage(cid, msg)
                    except Exception as e:
                        LOGGER.error(e)
    if path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        try:
            bot.edit_message_text("Restarted Successfully!", chat_id, msg_id)
        except:
            pass
        remove(".restartmsg")

    start_handler = CommandHandler(BotCommands.StartCommand, start)
    log_handler = CommandHandler(BotCommands.LogCommand, log,
                                        filters=CustomFilters.owner_filter | CustomFilters.sudo_user)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                        filters=CustomFilters.owner_filter | CustomFilters.sudo_user)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
    help_handler = CommandHandler(BotCommands.HelpCommand, bot_help,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
    stats_handler = CommandHandler(BotCommands.StatsCommand, stats,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)

    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)

app.start()
main()
main_loop.run_forever()