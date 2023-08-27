from init_bot import bot
from loguru import logger
import time
from core.config import config
import handlers
from db.sqlite import SQLite
from db.init_db import db


def main() -> None:
    """
    Функция запускает бота
    """
    logger.add(
        'logs/logs.log',
        level='DEBUG',
        format="{time} {level} {message}",
        rotation='1 week',
        retention='1 week',
        compression='zip'
    )

    with SQLite(db) as sqlite:
        sqlite.init_tables()

    while True:
        try:
            logger.info("Запуск бота")
            bot.run(config.BOT_TOKEN)
        except KeyboardInterrupt:
            logger.info("Завершение работы")
            exit()
            return
        except Exception as error:
            logger.info(f"Ошибка - {error}")
            time.sleep(1)


if __name__ == '__main__':
    main()
