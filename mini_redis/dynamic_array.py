"""고정 길이 list를 저장 공간으로만 사용하는 동적 배열."""


class DynamicArray:
    """공간이 부족할 때 용량을 두 배로 늘리는 배열."""

    def __init__(self, capacity=4):
        self.capacity = max(1, capacity)
        self._items = [None] * self.capacity
        self._size = 0

    def __len__(self):
        return self._size

    def _check(self, index):
        if index < 0 or index >= self._size:
            raise IndexError("array index out of range")

    def get(self, index):
        self._check(index)
        return self._items[index]

    def set(self, index, value):
        self._check(index)
        self._items[index] = value

    def append(self, value):
        if self._size == self.capacity:
            new_items = [None] * (self.capacity * 2)
            for index in range(self._size):
                new_items[index] = self._items[index]
            self._items = new_items
            self.capacity *= 2
        self._items[self._size] = value
        self._size += 1

    def remove(self, index):
        """중간 삭제는 O(n), 마지막 원소 삭제는 O(1)."""
        self._check(index)
        value = self._items[index]
        for current in range(index, self._size - 1):
            self._items[current] = self._items[current + 1]
        self._size -= 1
        self._items[self._size] = None
        return value
