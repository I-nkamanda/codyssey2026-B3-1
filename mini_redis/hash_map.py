"""직접 만든 해시 함수와 연결 리스트 체이닝을 사용하는 해시맵."""

from .linked_list import DoublyLinkedList


class HashMap:
    """평균 O(1) 조회. 로드 팩터가 0.75를 넘으면 버킷을 두 배로 확장."""

    def __init__(self, capacity=8):
        self.capacity = max(1, capacity)
        self._buckets = self._new_buckets(self.capacity)
        self._size = 0

    @staticmethod
    def _new_buckets(capacity):
        buckets = [None] * capacity
        for index in range(capacity):
            buckets[index] = DoublyLinkedList()
        return buckets

    @staticmethod
    def _hash(key):
        """UTF-8 각 바이트를 31진수처럼 누적하고 64비트 안에 유지한다."""
        result = 0
        for byte in key.encode("utf-8"):
            result = (result * 31 + byte) & 0xFFFFFFFFFFFFFFFF
        return result

    def _bucket(self, key):
        return self._buckets[self._hash(key) % self.capacity]

    def _find(self, key):
        node = self._bucket(key).head
        while node is not None:
            if node.data[0] == key:
                return node
            node = node.next
        return None

    def put(self, key, value):
        node = self._find(key)
        if node is not None:
            node.data = (key, value)
            return
        self._bucket(key).insert_back((key, value))
        self._size += 1
        if self._size * 4 > self.capacity * 3:
            self._resize()

    def _resize(self):
        previous = self._buckets
        self.capacity *= 2
        self._buckets = self._new_buckets(self.capacity)
        for bucket in previous:
            node = bucket.head
            while node is not None:
                self._bucket(node.data[0]).insert_back(node.data)
                node = node.next

    def get(self, key, default=None):
        node = self._find(key)
        return default if node is None else node.data[1]

    def remove(self, key):
        node = self._find(key)
        if node is None:
            return None
        self._bucket(key).remove_node(node)
        self._size -= 1
        return node.data[1]

    def contains(self, key):
        return self._find(key) is not None

    def keys(self):
        """키를 하나씩 반환한다. 출력 순서는 보장하지 않는다."""
        for bucket in self._buckets:
            node = bucket.head
            while node is not None:
                yield node.data[0]
                node = node.next

    def size(self):
        return self._size
