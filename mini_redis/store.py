"""문자열 저장, LRU 메모리 제한, TTL 만료를 조합하는 저장소."""

import time

from .hash_map import HashMap
from .linked_list import DoublyLinkedList
from .min_heap import MinHeap


class Entry:
    """하나의 키와 값, 바이트 크기, 만료 시각, LRU 노드를 보관한다."""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.byte_size = len(key.encode("utf-8")) + len(value.encode("utf-8"))
        self.expire_at = None
        self.lru_node = None


class MiniRedis:
    """명령 직전 만료를 정리한다. clock 주입으로 기다림 없이 테스트 가능."""

    def __init__(self, clock=None):
        self.data = HashMap()
        self.lru = DoublyLinkedList()
        self.expirations = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0
        self._clock = time.monotonic if clock is None else clock

    def _delete(self, key):
        entry = self.data.remove(key)
        if entry is None:
            return False
        self.lru.remove_node(entry.lru_node)
        self.expirations.remove(key)
        self.used_memory -= entry.byte_size
        return True

    def _purge_expired(self, now=None):
        now = self._clock() if now is None else now
        while self.expirations.peek() is not None:
            expire_at, key = self.expirations.peek()
            if expire_at > now:
                break
            self._delete(key)

    def _evict(self):
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            self._delete(self.lru.tail.data)
            self.evicted_keys += 1

    def set(self, key, value):
        self._purge_expired()
        incoming = Entry(key, value)
        if self.maxmemory > 0 and incoming.byte_size > self.maxmemory:
            raise MemoryError("command not allowed when used_memory > 'maxmemory'")
        self._delete(key)
        incoming.lru_node = self.lru.insert_front(key)
        self.data.put(key, incoming)
        self.used_memory += incoming.byte_size
        self._evict()

    def get(self, key):
        self._purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return None
        self.lru.move_to_front(entry.lru_node)
        return entry.value

    def delete(self, key):
        self._purge_expired()
        return int(self._delete(key))

    def exists(self, key):
        self._purge_expired()
        return int(self.data.contains(key))

    def dbsize(self):
        self._purge_expired()
        return self.data.size()

    def keys(self):
        self._purge_expired()
        return self.data.keys()

    def configure_maxmemory(self, byte_limit):
        if byte_limit < 0:
            raise ValueError("memory limit must be nonnegative")
        self._purge_expired()
        self.maxmemory = byte_limit
        self._evict()

    def memory_info(self):
        self._purge_expired()
        return (self.used_memory, self.maxmemory, self.evicted_keys)

    def expire(self, key, seconds):
        now = self._clock()
        self._purge_expired(now)
        entry = self.data.get(key)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete(key)
        else:
            entry.expire_at = now + seconds
            self.expirations.push((entry.expire_at, key))
        return 1

    def ttl(self, key):
        now = self._clock()
        self._purge_expired(now)
        entry = self.data.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        return int(entry.expire_at - now)
