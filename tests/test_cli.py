"""명령 문법, 출력 형식, 실제 프로그램 실행을 검증한다."""

import subprocess
import sys
import unittest

from mini_redis.cli import CommandProcessor, INTEGER_ERROR


class CliTests(unittest.TestCase):
    def test_successful_commands(self):
        cli = CommandProcessor()
        pairs = (
            ('set name "Alice Kim"', 'OK'),
            ('GET name', '"Alice Kim"'),
            ('EXISTS name', '(integer) 1'),
            ('DBSIZE', '(integer) 1'),
            ('KEYS', '1. "name"'),
            ('TTL name', '(integer) -1'),
            ('EXPIRE missing 3', '(integer) 0'),
            ('EXPIRE name 0', '(integer) 1'),
            ('GET name', '(nil)'),
            ('DEL name', '(integer) 0'),
            ('KEYS', '(empty array)'),
            ('SET "" ""', 'OK'),
            ('GET ""', '""'),
            ('DEL ""', '(integer) 1'),
            ('CONFIG SET maxmemory 30', 'OK'),
            ('INFO memory', 'used_memory:0\nmaxmemory:30\nevicted_keys:0'),
            ('  ', ''),
            ('QUIT', None),
            ('exit', None),
        )
        for command, expected in pairs:
            self.assertEqual(cli.execute(command), expected, command)

    def test_errors_and_recovery(self):
        cli = CommandProcessor()
        pairs = (
            ('HELLO', "(error) ERR unknown command 'HELLO'"),
            ('GET', "(error) ERR wrong number of arguments for 'GET' command"),
            ('SET a', "(error) ERR wrong number of arguments for 'SET' command"),
            ('KEYS *', "(error) ERR wrong number of arguments for 'KEYS' command"),
            ('SET a "oops', '(error) ERR invalid quoting'),
            ('CONFIG GET maxmemory 2', '(error) ERR unsupported CONFIG option'),
            ('INFO cpu', '(error) ERR unsupported INFO section'),
        )
        for command, expected in pairs:
            self.assertEqual(cli.execute(command), expected)
        for token in ('abc', '1.5', '1_000', '１２', '9223372036854775808', '-9223372036854775809', '9' * 5000):
            self.assertEqual(cli.execute('EXPIRE missing ' + token), INTEGER_ERROR)
        self.assertEqual(cli.execute('CONFIG SET maxmemory -1'), INTEGER_ERROR)
        self.assertEqual(cli.execute('CONFIG SET maxmemory 1'), 'OK')
        self.assertEqual(cli.execute('SET a b'), "(error) OOM command not allowed when used_memory > 'maxmemory'")
        self.assertEqual(cli.execute('CONFIG SET maxmemory 0'), 'OK')
        self.assertEqual(cli.execute('SET a b'), 'OK')

    def test_quotes_unicode_and_hash_character(self):
        cli = CommandProcessor()
        self.assertEqual(cli.execute('SET 이름 "김 철수"'), 'OK')
        self.assertEqual(cli.execute('GET 이름'), '"김 철수"')
        self.assertEqual(cli.execute('SET x "a\\\"b"'), 'OK')
        self.assertEqual(cli.execute('GET x'), '"a\\\"b"')
        self.assertEqual(cli.execute('SET x #tag'), 'OK')
        self.assertEqual(cli.execute('GET x'), '"#tag"')

    def test_real_repl_and_eof(self):
        for commands in ('SET a "hello world"\nGET a\nquit\n', 'SET a "hello world"\nGET a\n'):
            result = subprocess.run(
                [sys.executable, '-m', 'mini_redis'], input=commands,
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('mini-redis> OK', result.stdout)
            self.assertIn('mini-redis> "hello world"', result.stdout)
