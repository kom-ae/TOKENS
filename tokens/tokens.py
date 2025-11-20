import subprocess
from pathlib import Path

from PyKCS11 import PyKCS11Error, PyKCS11Lib, Session
from PyKCS11.constants import CKF_RW_SESSION, CKU_SO

from constants import (LIST_PIN_ADMIN, MAX_PIN_COUNT_SO, MAX_PIN_COUNT_USER,
                       MIN_SO_PIN, MIN_USER_PIN, MODE_CHANGE_PIN, PIN_ADMIN,
                       TOKEN_CONF)
from tokens.exceptions import FormatException
from tokens.pkcs11_custom import PyKCS11LibCustom


class Token:
    """Базовый класс токена."""

    def __init__(
            self,
            lib_path: str,
            serial_num: str,
            min_pin_user: int,
            label: str,
            slot: int
    ):
        """
        Args:
            lib_path (str): путь до библиотеки для управления токеном
            serial_num (str): Серийный номер токена
            min_pin_user (int): Текущая минимальная длина пин кода
        """
        self.lib_path = lib_path
        self.serial_num_raw = serial_num
        self.serial_num = serial_num
        self.label = label
        self.min_pin_user = min_pin_user
        self.slot = slot


class Rutoken(Token):
    """Базовый класс для Рутокена.

    В базовом классе для форматирования используется утилита rtadmin
    версии 1.3. Утилита этой версии форматирует токены Rutoken S,
    Rutoken lite, Rutoken ЭЦП 3.0(на остальных не проверялось).
    Для использования всего функционала утилиты rtadmin,
    необходимо использовать соответствующую версию и переопределить
    методы в дочерних классах.

    """

    token_conf: dict = TOKEN_CONF.get('Rutoken S')
    if token_conf:
        rtadmin: Path = token_conf.get('rtadmin_path')

    def __init__(self, lib_path, serial_num, min_pin_user, label, slot):
        super().__init__(lib_path, serial_num, min_pin_user, label, slot)
        self.serial_num = int(self.serial_num_raw, 16)

    def format(self, user_pin: str, label: str):
        """Форматирует токен."""
        if not self.rtadmin.is_file():
            raise FileNotFoundError(f'Файл {self.rtadmin._str} не найден.')

        try:
            return subprocess.run(
                f'{self.rtadmin} -f -a {PIN_ADMIN} -u {user_pin} \
                    -p {MODE_CHANGE_PIN} -M {MIN_SO_PIN} -m {MIN_USER_PIN} \
                    -R {MAX_PIN_COUNT_SO} -r {MAX_PIN_COUNT_USER} \
                    -D {label} -q -z {self.lib_path}',
                capture_output=True,
                text=True,
                check=True
            ).stdout
        except subprocess.CalledProcessError as err:
            raise FormatException(f'{err.returncode}: {err.stderr}')


class RutokenS(Rutoken):
    """Для токена Rutoken S."""

    model = 'Rutoken S'


class RutokenLite(Rutoken):
    """Для токена Rutoken lite."""

    model = 'Rutoken lite'

    token_conf: dict = TOKEN_CONF.get('Rutoken lite')
    if token_conf:
        rtadmin: Path = token_conf.get('rtadmin_path')

    def format(self, user_pin: str, label: str):
        """Форматирует токен."""
        if not self.rtadmin.is_file():
            raise FileNotFoundError(f'Файл {self.rtadmin._str} не найден.')

        try:
            return subprocess.run(
                f'{self.rtadmin} format --repair --new-so-pin {PIN_ADMIN} \
                    --new-user-pin {user_pin} -l {label} \
                    --min-so-pin {MIN_SO_PIN} --min-user-pin {MIN_USER_PIN} \
                    --max-user-pin-retry-count {MAX_PIN_COUNT_USER} \
                    --max-so-pin-retry-count {MAX_PIN_COUNT_SO} \
                    --pin-change-policy both -s {self.serial_num}',
                capture_output=True,
                text=True,
                check=True
            ).stdout
        except subprocess.CalledProcessError as err:
            raise FormatException(f'{err.returncode}: {err.stderr}')


class RutokenECP(Rutoken):
    """Для токена Rutoken ЭЦП."""

    model = 'Rutoken ЭЦП'

    token_conf: dict = TOKEN_CONF.get('Rutoken ECP')
    if token_conf:
        rtadmin: Path = token_conf.get('rtadmin_path')

    def format(self, user_pin: str, label: str):
        """Форматирует токен."""
        if not self.rtadmin.is_file():
            raise FileNotFoundError(f'Файл {self.rtadmin._str} не найден.')
        try:
            return subprocess.run(
                f'{self.rtadmin} format --repair --new-so-pin {PIN_ADMIN} \
                    --new-user-pin {user_pin} -l {label} \
                    --min-so-pin {MIN_SO_PIN} --min-user-pin {MIN_USER_PIN} \
                    --max-user-pin-retry-count {MAX_PIN_COUNT_USER} \
                    --max-so-pin-retry-count {MAX_PIN_COUNT_SO} \
                    --pin-change-policy both -s {self.serial_num}',
                capture_output=True,
                text=True,
                check=True
            ).stdout
        except subprocess.CalledProcessError as err:
            raise FormatException(f'{err.returncode}: {err.stderr}')


class JaCartaLaser(Token):
    """Токен JaCatra PKI."""

    model = 'JaCarta PKI'
    current_pin: str = ''

    def __set_current_pin(self, session: Session):
        """Возвращает текущий pin токена перебором из LIST_PIN_ADMIN."""
        for pin in LIST_PIN_ADMIN:
            try:
                session.login(pin, CKU_SO)
                self.current_pin = pin
                session.logout()
                break
            except PyKCS11Error:
                continue

    def format(self, user_pin: str, label: str):
        """Форматирование JaCatra PKI и установка пин кодов."""
        pkcs11 = PyKCS11Lib().load(self.lib_path)
        pkcs11.getSlotList(tokenPresent=True)
        try:
            info = pkcs11.getTokenInfo(self.slot)
        except PyKCS11Error as err:
            FormatException(str(err))
        if self.serial_num_raw != str(info.serialNumber).strip():
            raise FormatException(('Устройство с серийным номером '
                              f'{self.serial_num_raw} извлечено.'))
        session = pkcs11.openSession(self.slot, CKF_RW_SESSION)
        self.__set_current_pin(session)
        # Закрываем сессию для инициализации токена.
        session.closeSession()
        if not self.current_pin:
            raise FormatException('Пин код не удалось подобрать.')
        pkcs = PyKCS11LibCustom(self.lib_path)
        pkcs.initToken(self.slot, self.current_pin, label)
        del pkcs
        session = pkcs11.openSession(self.slot, CKF_RW_SESSION)
        session.login(self.current_pin, CKU_SO)
        session.initPin(user_pin)
        session.closeSession()


tokens_classes = {
    'Rutoken S': RutokenS,
    'Rutoken lite': RutokenLite,
    'Rutoken ECP': RutokenECP,
    'JaCarta Laser': JaCartaLaser,
}
