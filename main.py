from telegram.ext import Application, CommandHandler

from handlers import add_data, conv_handler, start
from settings import settings


def main() -> None:
    application = (Application.builder().token(settings.bot_token.get_secret_value()).proxy(settings.proxy_url)
                   .get_updates_proxy(settings.proxy_url)
                   .build())
    application.add_handler(CommandHandler('add_data', add_data))
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
