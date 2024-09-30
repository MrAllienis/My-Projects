import datetime
from typing import Any, Union

import numpy as np


class GSheetUtils:
    @staticmethod
    def parse_bool(value: Any) -> bool:
        """Парсинг значения Да/Нет из ячейки таблицы"""

        if value in {True, False}:
            return value

        if isinstance(value, str):
            value = value.strip()

            if all(x in "0123456789.," for x in value):
                try:
                    value = float(value.replace(",", "."))
                except ValueError:
                    return False
            else:
                return value.lower() in {"true", "да", "yes", "y"}

        if isinstance(value, int) or isinstance(value, float):
            if np.isnan(value):
                return False

            return bool(value)

        return False

    @staticmethod
    def parse_datetime(value: Union[int, str, datetime.datetime]) -> datetime.datetime:
        """Парсинг datetime из ячейки таблицы"""

        if not value:
            return None

        if isinstance(value, datetime.datetime):
            return value

        if isinstance(value, int) or isinstance(value, float):
            return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=value)

        if isinstance(value, str):
            value_strip = value.strip()

            for format in (
                    "%d.%m.%Y",
                    "%d.%m.%Y %H:%M",
                    "%d.%m.%Y %H:%M:%S"
            ):
                try:
                    return datetime.datetime.strptime(value_strip, format)
                except:
                    pass

        return None


if __name__ == "__main__":
    # test parse_bool
    assert GSheetUtils.parse_bool(" Да")
    assert not GSheetUtils.parse_bool("нЕт  ")
    assert not GSheetUtils.parse_bool("nein!")
    assert GSheetUtils.parse_bool("yes")
    assert GSheetUtils.parse_bool("y")
    assert GSheetUtils.parse_bool("TRUE")
    assert not GSheetUtils.parse_bool("false")
    assert GSheetUtils.parse_bool(1)
    assert GSheetUtils.parse_bool(-2)
    assert GSheetUtils.parse_bool("5")
    assert GSheetUtils.parse_bool(True)
    assert not GSheetUtils.parse_bool(False)
    assert not GSheetUtils.parse_bool("0  ")
    assert GSheetUtils.parse_bool("0.1")
    assert GSheetUtils.parse_bool(0.1)
    assert not GSheetUtils.parse_bool(".....")
    assert not GSheetUtils.parse_bool(np.nan)

    # test parse_datetime
    test_datetime = datetime.datetime.now().replace(microsecond=0)

    assert GSheetUtils.parse_datetime(None) == None
    assert GSheetUtils.parse_datetime(test_datetime) == test_datetime
    assert GSheetUtils.parse_datetime(test_datetime.strftime("  " + "%d.%m.%Y") + "   ") == test_datetime.replace(
        hour=0, minute=0, second=0)
    assert GSheetUtils.parse_datetime(test_datetime.strftime("%d.%m.%Y %H:%M")) == test_datetime.replace(second=0)
    assert GSheetUtils.parse_datetime(test_datetime.strftime("%d.%m.%Y %H:%M:%S")) == test_datetime
    assert GSheetUtils.parse_datetime(45394.5878880903).replace(microsecond=0) == datetime.datetime.strptime(
        "12.04.2024 14:06:33", "%d.%m.%Y %H:%M:%S")