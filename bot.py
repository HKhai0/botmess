from fbchat_muqit import Client, Message, ThreadType
import asyncio
import logging
import sys

# --- Cấu hình logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("fbchat")

# --- Cấu hình bot ---
AUTO_REPLY_ENABLED = True  # True: tự động trả lời menu, False: không trả lời
VALID_COMMANDS = ["menu", "1", "2", "3", "help", "exit"]  # chỉ những lệnh hợp lệ mới xử lý

class MenuBot(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread_state = {}  # trạng thái per-thread (thread_id -> state)
        self.MAIN_MENU_TEXT = (
            "📋 *Menu chính*\n"
            "1. Thông tin tài khoản\n"
            "2. Hướng dẫn sử dụng\n"
            "3. Liên hệ hỗ trợ\n"
            "Gõ số 1-3 hoặc 'help' để xem lại menu."
        )

    # --- các hàm xử lý menu ---
    async def send_main_menu(self, thread_id, thread_type, reply_to_id=None):
        if AUTO_REPLY_ENABLED:
            await self.sendMessage(self.MAIN_MENU_TEXT, thread_id, thread_type, reply_to_id=reply_to_id)

    async def handle_account_info(self, mid, author_id, message_object, thread_id, thread_type):
        if AUTO_REPLY_ENABLED:
            text = f"🔐 Thông tin tài khoản:\n- UID: {author_id}\n- Trạng thái: Hoạt động\n\nGõ 'menu' để về menu chính."
            await self.sendMessage(text, thread_id, thread_type, reply_to_id=mid)

    async def handle_guide(self, mid, author_id, message_object, thread_id, thread_type):
        if AUTO_REPLY_ENABLED:
            text = "📘 Hướng dẫn sử dụng:\n• Gõ 'menu' để xem menu.\n• Chọn 1/2/3 tương ứng.\n• Gõ 'exit' để thoát."
            await self.sendMessage(text, thread_id, thread_type, reply_to_id=mid)

    async def handle_support(self, mid, author_id, message_object, thread_id, thread_type):
        if AUTO_REPLY_ENABLED:
            text = "📞 Hỗ trợ:\nLiên hệ: +84 90x xxx xxx\nEmail: support@example.com\nGõ 'menu' để về menu chính."
            await self.sendMessage(text, thread_id, thread_type, reply_to_id=mid)

    # --- sự kiện tin nhắn ---
    async def onMessage(self, mid, author_id: str, message_object: Message, thread_id, thread_type=ThreadType.USER, **kwargs):
        try:
            # lấy text từ message
            text = getattr(message_object, "text", None) or getattr(message_object, "body", "")
            text_norm = text.strip().lower()
            logger.info(f"Received message: mid={mid} author={author_id} thread={thread_id} text={repr(text)}")

            # bỏ qua tin nhắn từ bot
            if author_id == self.uid:
                return

            # chỉ xử lý nếu tin nhắn là lệnh hợp lệ
            if text_norm not in VALID_COMMANDS:
                logger.info(f"Ignored invalid command: {text_norm}")
                return

            # xử lý các lệnh hợp lệ
            if text_norm in ("menu", "help"):
                self.thread_state[thread_id] = "AWAITING_CHOICE"
                await self.send_main_menu(thread_id, thread_type, reply_to_id=mid)
            elif text_norm == "1":
                await self.handle_account_info(mid, author_id, message_object, thread_id, thread_type)
            elif text_norm == "2":
                await self.handle_guide(mid, author_id, message_object, thread_id, thread_type)
            elif text_norm == "3":
                await self.handle_support(mid, author_id, message_object, thread_id, thread_type)
            elif text_norm == "exit":
                self.thread_state.pop(thread_id, None)
                if AUTO_REPLY_ENABLED:
                    await self.sendMessage("✅ Đã thoát menu. Gõ 'menu' để mở lại.", thread_id, thread_type, reply_to_id=mid)

        except Exception as e:
            logger.exception("Error in onMessage: %s", e)

# --- main ---
async def main():
    cookies_path = "cookie.json"
    bot = await MenuBot.startSession(cookies_path)

    if not await bot.isLoggedIn():
        logger.error("Login failed — cookie sai hoặc hết hạn.")
        return

    try:
        fetch_client_info = await bot.fetchUserInfo(bot.uid)
        client_info = fetch_client_info.get(bot.uid) if fetch_client_info else None
        if client_info:
            logger.info("Logged in as %s (uid=%s)", client_info.name, bot.uid)
        else:
            logger.info("Logged in (uid=%s) nhưng không fetch được thông tin user", bot.uid)
    except Exception as e:
        logger.warning("Không thể fetchUserInfo: %s", e)

    try:
        logger.info("Start listening...")
        await bot.listen()
    except Exception as e:
        logger.exception("Error while listening: %s", e)
    finally:
        try:
            if hasattr(bot, "session") and bot.session:
                await bot.session.close()
                logger.info("Closed aiohttp session")
        except Exception:
            pass

asyncio.run(main())
