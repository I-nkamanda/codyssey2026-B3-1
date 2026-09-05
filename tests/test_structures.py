"""자료구조의 경계 조건과 무작위 연산 뒤 불변식을 검사한다."""

import random
import unittest

from mini_redis.dynamic_array import DynamicArray
from mini_redis.hash_map import HashMap
from mini_redis.linked_list import DoublyLinkedList, Node
from mini_redis.min_heap import MinHeap


class ArrayTests(unittest.TestCase):
    def test_growth_and_removal(self):
        array = DynamicArray(1)
        for i in range(17):
            array.append(i)
        self.assertEqual(array.capacity, 32)
        self.assertEqual(array.remove(4), 4)
        self.assertEqual(array.get(4), 5)
        array.set(0, 99)
        self.assertEqual(array.get(0), 99)
        while len(array):
            array.remove(len(array) - 1)
        with self.assertRaises(IndexError):
            array.get(0)
        with self.assertRaises(IndexError):
            array.set(-1, 0)


class ListTests(unittest.TestCase):
    def test_all_operations_and_identity(self):
        linked = DoublyLinkedList()
        self.assertIsNone(linked.remove_front())
        self.assertIsNone(linked.remove_back())
        a = linked.insert_front("a")
        b = linked.insert_back("b")
        c = linked.insert_front("c")
        linked.move_to_front(b)
        self.assertIs(linked.head, b)
        self.assertIs(b.next, c)
        self.assertIs(c.prev, b)
        self.assertEqual(linked.remove_node(c), "c")
        self.assertIs(b.next, a)
        self.assertIs(a.prev, b)
        linked.move_to_front(b)
        self.assertEqual(linked.remove_back(), "a")
        self.assertEqual(linked.remove_front(), "b")
        self.assertEqual(linked.size, 0)
        self.assertIsNone(linked.head)
        self.assertIsNone(linked.tail)
        with self.assertRaises(ValueError):
            linked.remove_node(c)
        with self.assertRaises(ValueError):
            linked.move_to_front(Node("foreign"))


class MapTests(unittest.TestCase):
    def test_collision_update_delete(self):
        mapping = HashMap()
        # 이 해시 함수에서 Aa와 BB는 같은 해시를 갖는다.
        self.assertEqual(mapping._hash("Aa"), mapping._hash("BB"))
        mapping.put("Aa", 1)
        mapping.put("BB", 2)
        mapping.put("Aa", 3)
        self.assertEqual(mapping.size(), 2)
        self.assertEqual(mapping.remove("Aa"), 3)
        self.assertEqual(mapping.get("BB"), 2)
        self.assertIsNone(mapping.remove("missing"))

    def test_resize_and_unicode(self):
        mapping = HashMap(4)
        for i in range(3):
            mapping.put(str(i), i)
        self.assertEqual(mapping.capacity, 4)
        mapping.put("한글", None)
        self.assertEqual(mapping.capacity, 8)
        self.assertTrue(mapping.contains("한글"))
        for i in range(1000):
            mapping.put(str(i), i)
        for i in range(1000):
            self.assertEqual(mapping.get(str(i)), i)
        self.assertEqual(mapping.size(), 1001)
        self.assertEqual(len(tuple(mapping.keys())), 1001)


class HeapTests(unittest.TestCase):
    def test_order_ties_and_replacement(self):
        heap = MinHeap()
        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())
        for item in ((3, "c"), (1, "b"), (1, "a"), (9, "d")):
            heap.push(item)
        heap.push((0, "c"))
        self.assertEqual(heap.size(), 4)
        self.assertEqual(heap.remove("d"), (9, "d"))
        self.assertEqual(heap.pop(), (0, "c"))
        self.assertEqual(heap.pop(), (1, "a"))
        self.assertEqual(heap.pop(), (1, "b"))
        self.assertEqual(heap._positions.size(), 0)

    def test_randomized_updates_removals_and_pops(self):
        rng = random.Random(42)
        heap = MinHeap()
        expected = [None] * 80
        for step in range(3000):
            index = rng.randrange(80)
            key = str(index)
            action = rng.randrange(3)
            if action == 0:
                item = (rng.randrange(200), key)
                heap.push(item)
                expected[index] = item
            elif action == 1:
                self.assertEqual(heap.remove(key), expected[index])
                expected[index] = None
            else:
                candidates = [item for item in expected if item is not None]
                first = min(candidates) if candidates else None
                self.assertEqual(heap.pop(), first)
                if first is not None:
                    expected[int(first[1])] = None
            active = [item for item in expected if item is not None]
            self.assertEqual(heap.size(), len(active))
            self.assertEqual(heap.peek(), min(active) if active else None)
            self.assertEqual(heap._positions.size(), heap.size())
            for i in range(heap.size()):
                item = heap._items.get(i)
                self.assertEqual(heap._positions.get(item[1]), i)
                if i:
                    self.assertLessEqual(heap._items.get((i - 1) // 2), item)
