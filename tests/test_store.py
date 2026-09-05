"""가짜 시계로 TTL을 정확하고 빠르게 검증한다."""

import random
import unittest

from mini_redis.store import MiniRedis


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.store = MiniRedis(self.clock)

    def assert_consistent(self):
        store = self.store
        self.assertEqual(store.data.size(), store.lru.size)
        used = 0
        ttl_count = 0
        for key in store.data.keys():
            entry = store.data.get(key)
            used += entry.byte_size
            self.assertEqual(entry.lru_node.data, key)
            self.assertIs(entry.lru_node.owner, store.lru)
            if entry.expire_at is not None:
                ttl_count += 1
                index = store.expirations._positions.get(key)
                self.assertIsNotNone(index)
                self.assertEqual(store.expirations._items.get(index), (entry.expire_at, key))
        self.assertEqual(used, store.used_memory)
        self.assertEqual(ttl_count, store.expirations.size())
        if store.maxmemory:
            self.assertLessEqual(used, store.maxmemory)
        node = store.lru.head
        previous = None
        count = 0
        while node is not None:
            self.assertIs(node.prev, previous)
            self.assertIs(store.data.get(node.data).lru_node, node)
            previous = node
            node = node.next
            count += 1
            self.assertLessEqual(count, store.data.size())
        self.assertIs(previous, store.lru.tail)
        self.assertEqual(count, store.data.size())

    def test_basic_and_empty_strings(self):
        self.assertIsNone(self.store.get("missing"))
        self.assertEqual(self.store.delete("missing"), 0)
        self.store.set("", "")
        self.assertEqual(self.store.get(""), "")
        self.assertEqual(self.store.dbsize(), 1)
        self.assertEqual(self.store.used_memory, 0)
        self.assertEqual(tuple(self.store.keys()), ("",))
        self.assertEqual(self.store.delete(""), 1)
        self.assert_consistent()

    def test_utf8_and_overwrite_accounting(self):
        self.store.set("이름", "철수")
        self.assertEqual(self.store.used_memory, 12)
        self.store.set("이름", "A")
        self.assertEqual(self.store.used_memory, 7)
        self.store.delete("이름")
        self.assertEqual(self.store.used_memory, 0)

    def test_mission_example(self):
        self.store.configure_maxmemory(30)
        self.store.set("user:1", "Alice")
        self.store.set("user:2", "Bob")
        self.store.set("user:3", "Charlie")
        self.assertIsNone(self.store.get("user:1"))
        self.assertEqual(self.store.memory_info(), (22, 30, 1))
        self.assert_consistent()

    def test_get_updates_lru_and_multiple_evictions(self):
        self.store.configure_maxmemory(6)
        for key in ("a", "b", "c"):
            self.store.set(key, "1")
        self.store.get("a")
        self.store.set("d", "1")
        self.assertEqual(self.store.exists("b"), 0)
        self.store.set("big", "123")
        self.assertEqual(tuple(self.store.keys()), ("big",))
        self.assertEqual(self.store.evicted_keys, 4)
        self.assert_consistent()

    def test_non_get_commands_do_not_touch_lru(self):
        for key in ("a", "b"):
            self.store.set(key, "1")
        self.store.exists("a")
        self.store.expire("a", 5)
        self.store.ttl("a")
        tuple(self.store.keys())
        self.store.dbsize()
        self.store.memory_info()
        self.assertEqual(self.store.lru.tail.data, "a")

    def test_set_updates_lru_and_resets_ttl(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("a", 1)
        self.store.set("a", "3")
        self.assertEqual(self.store.lru.head.data, "a")
        self.assertEqual(self.store.ttl("a"), -1)
        self.assertEqual(self.store.expirations.size(), 0)
        self.clock.now += 2
        self.assertEqual(self.store.get("a"), "3")

    def test_oom_preserves_existing_value_ttl_and_order(self):
        self.store.configure_maxmemory(4)
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("a", 5)
        with self.assertRaises(MemoryError):
            self.store.set("a", "12345")
        with self.assertRaises(MemoryError):
            self.store.set("new", "12345")
        self.assertEqual(self.store.lru.tail.data, "a")
        self.assertEqual(self.store.ttl("a"), 5)
        self.assertEqual(self.store.get("a"), "1")
        self.assertEqual(self.store.memory_info(), (4, 4, 0))
        self.assert_consistent()

    def test_config_reduces_immediately_and_zero_is_unlimited(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.configure_maxmemory(2)
        self.assertEqual(self.store.exists("a"), 0)
        self.store.configure_maxmemory(0)
        self.store.set("long", "long value")
        self.assertEqual(self.store.exists("long"), 1)
        with self.assertRaises(ValueError):
            self.store.configure_maxmemory(-1)

    def test_ttl_boundaries(self):
        self.assertEqual(self.store.ttl("a"), -2)
        self.assertEqual(self.store.expire("a", 3), 0)
        self.store.set("a", "1")
        self.assertEqual(self.store.ttl("a"), -1)
        self.assertEqual(self.store.expire("a", 3), 1)
        self.assertEqual(self.store.ttl("a"), 3)
        self.clock.now += 0.25
        self.assertEqual(self.store.ttl("a"), 2)
        self.clock.now += 2.75
        self.assertIsNone(self.store.get("a"))
        self.assertEqual(self.store.ttl("a"), -2)
        self.assertEqual(self.store.memory_info(), (0, 0, 0))
        self.assert_consistent()

    def test_expire_renewal_and_immediate_expiration(self):
        self.store.set("a", "1")
        for seconds in range(1, 101):
            self.store.expire("a", seconds)
            self.assertEqual(self.store.expirations.size(), 1)
        self.clock.now += 2
        self.assertEqual(self.store.get("a"), "1")
        self.store.expire("a", 0)
        self.assertEqual(self.store.exists("a"), 0)
        self.store.set("a", "1")
        self.store.expire("a", -5)
        self.assertEqual(self.store.exists("a"), 0)
        self.assert_consistent()

    def test_delete_and_recreate_cancels_old_ttl(self):
        self.store.set("a", "old")
        self.store.expire("a", 1)
        self.store.delete("a")
        self.assertEqual(self.store.expirations.size(), 0)
        self.store.set("a", "new")
        self.clock.now += 2
        self.assertEqual(self.store.get("a"), "new")
        self.assert_consistent()

    def test_all_reads_purge_expired_keys(self):
        for operation in ("get", "exists", "delete", "ttl", "expire", "keys", "dbsize", "memory_info"):
            self.store = MiniRedis(self.clock)
            self.store.set("a", "1")
            self.store.expire("a", 1)
            self.clock.now += 1
            if operation in ("keys", "dbsize", "memory_info"):
                getattr(self.store, operation)()
            elif operation == "expire":
                self.store.expire("a", 5)
            else:
                getattr(self.store, operation)("a")
            self.assertEqual(self.store.data.size(), 0, operation)
            self.assert_consistent()

    def test_expiration_before_eviction(self):
        self.store.configure_maxmemory(4)
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("b", 1)
        self.clock.now += 1
        self.store.set("c", "3")
        self.assertEqual(self.store.exists("a"), 1)
        self.assertEqual(self.store.evicted_keys, 0)
        self.store.expire("a", 5)
        self.store.set("d", "4")
        self.assertEqual(self.store.expirations.size(), 0)
        self.assert_consistent()

    def test_randomized_cross_structure_consistency(self):
        rng = random.Random(19)
        for step in range(2000):
            key = "key" + str(rng.randrange(40))
            action = rng.randrange(6)
            if action == 0:
                try:
                    self.store.set(key, "가" * rng.randrange(20))
                except MemoryError:
                    pass
            elif action == 1:
                self.store.get(key)
            elif action == 2:
                self.store.delete(key)
            elif action == 3:
                self.store.expire(key, rng.randrange(-1, 10))
            elif action == 4:
                self.clock.now += 0.5
                self.store.dbsize()
            else:
                self.store.configure_maxmemory(rng.randrange(100))
            self.assert_consistent()
