"""(expire_at, key)를 다루며 임의의 키도 삭제할 수 있는 최소 힙."""

from .dynamic_array import DynamicArray
from .hash_map import HashMap


class MinHeap:
    """키→배열 위치를 직접 만든 해시맵으로 추적해 TTL을 즉시 취소한다."""

    def __init__(self):
        self._items = DynamicArray()
        self._positions = HashMap()

    def size(self):
        return len(self._items)

    def peek(self):
        return None if self.size() == 0 else self._items.get(0)

    def _swap(self, left, right):
        a, b = self._items.get(left), self._items.get(right)
        self._items.set(left, b)
        self._items.set(right, a)
        self._positions.put(b[1], left)
        self._positions.put(a[1], right)

    def _heapify_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._items.get(parent) <= self._items.get(index):
                break
            self._swap(parent, index)
            index = parent

    def _heapify_down(self, index):
        while index * 2 + 1 < self.size():
            child = index * 2 + 1
            right = child + 1
            if right < self.size() and self._items.get(right) < self._items.get(child):
                child = right
            if self._items.get(index) <= self._items.get(child):
                break
            self._swap(index, child)
            index = child

    def push(self, item):
        """같은 키의 만료 시간을 교체하므로 키마다 힙 원소는 최대 하나다."""
        self.remove(item[1])
        self._positions.put(item[1], self.size())
        self._items.append(item)
        self._heapify_up(self.size() - 1)

    def pop(self):
        first = self.peek()
        if first is not None:
            self.remove(first[1])
        return first

    def remove(self, key):
        """마지막 원소로 빈칸을 채우고 위/아래 중 필요한 방향으로 복구한다."""
        index = self._positions.get(key)
        if index is None:
            return None
        removed = self._items.get(index)
        last = self._items.remove(self.size() - 1)
        self._positions.remove(key)
        if index < self.size():
            self._items.set(index, last)
            self._positions.put(last[1], index)
            parent = (index - 1) // 2
            if index > 0 and self._items.get(index) < self._items.get(parent):
                self._heapify_up(index)
            else:
                self._heapify_down(index)
        return removed
