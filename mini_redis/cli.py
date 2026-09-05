"""따옴표를 지원하는 명령 해석기와 대화형 입출력."""

import json
import re
import shlex

from .store import MiniRedis


INTEGER_ERROR = "(error) ERR value is not an integer or out of range"


def parse_integer(value, nonnegative=False):
    """ASCII 십진수와 선택적 부호만 허용하며 부호 있는 64비트로 제한."""
    if re.fullmatch(r"[+-]?[0-9]+", value) is None:
        raise ValueError(INTEGER_ERROR)
    number = int(value)
    if number < -(2 ** 63) or number > 2 ** 63 - 1:
        raise ValueError(INTEGER_ERROR)
    if nonnegative and number < 0:
        raise ValueError(INTEGER_ERROR)
    return number


def quote(value):
    """출력용 따옴표와 제어 문자 이스케이프. 한국어는 그대로 출력한다."""
    return json.dumps(value, ensure_ascii=False)


class CommandProcessor:
    """execute는 결과 문자열을 반환하며 종료 명령이면 None을 반환한다."""

    def __init__(self, store=None):
        self.store = MiniRedis() if store is None else store

    def execute(self, line):
        try:
            parts = shlex.split(line, comments=False, posix=True)
        except ValueError:
            return "(error) ERR invalid quoting"
        if not parts:
            return ""
        command = parts[0].upper()
        names = ("SET", "GET", "DEL", "EXISTS", "DBSIZE", "KEYS",
                 "CONFIG", "INFO", "EXPIRE", "TTL", "EXIT", "QUIT")
        counts = (3, 2, 2, 2, 1, 1, 4, 2, 3, 2, 1, 1)
        if command not in names:
            return "(error) ERR unknown command '{}'".format(parts[0])
        if len(parts) != counts[names.index(command)]:
            return "(error) ERR wrong number of arguments for '{}' command".format(command)
        try:
            return self._run(command, parts)
        except MemoryError as error:
            return "(error) OOM " + str(error)
        except ValueError:
            return INTEGER_ERROR

    def _run(self, command, parts):
        if command in ("EXIT", "QUIT"):
            return None
        if command == "SET":
            self.store.set(parts[1], parts[2])
            return "OK"
        if command == "GET":
            value = self.store.get(parts[1])
            return "(nil)" if value is None else quote(value)
        if command == "DEL":
            value = self.store.delete(parts[1])
        elif command == "EXISTS":
            value = self.store.exists(parts[1])
        elif command == "DBSIZE":
            value = self.store.dbsize()
        elif command == "TTL":
            value = self.store.ttl(parts[1])
        elif command == "EXPIRE":
            value = self.store.expire(parts[1], parse_integer(parts[2]))
        elif command == "KEYS":
            output = "\n".join("{}. {}".format(i, quote(key))
                               for i, key in enumerate(self.store.keys(), 1))
            return output or "(empty array)"
        elif command == "CONFIG":
            if parts[1].upper() != "SET" or parts[2].lower() != "maxmemory":
                return "(error) ERR unsupported CONFIG option"
            self.store.configure_maxmemory(parse_integer(parts[3], nonnegative=True))
            return "OK"
        elif command == "INFO":
            if parts[1].lower() != "memory":
                return "(error) ERR unsupported INFO section"
            used, limit, evicted = self.store.memory_info()
            return "used_memory:{}\nmaxmemory:{}\nevicted_keys:{}".format(used, limit, evicted)
        return "(integer) {}".format(value)


def main():
    """EOF 또는 Ctrl+C로도 안전하게 종료한다. 저장 내용은 메모리에만 있다."""
    processor = CommandProcessor()
    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        output = processor.execute(line)
        if output is None:
            break
        if output:
            print(output)
