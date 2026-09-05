"""노드의 위치를 알면 상수 시간에 삽입·삭제할 수 있는 리스트."""


class Node:
    """data와 양방향 연결을 보관한다."""

    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None
        self.owner = None


class DoublyLinkedList:
    """head가 맨 앞, tail이 맨 뒤이며 모든 변경 연산은 O(1)."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def insert_front(self, data):
        node = Node(data)
        self._attach_front(node)
        return node

    def _attach_front(self, node):
        node.owner = self
        node.prev = None
        node.next = self.head
        if self.head is None:
            self.tail = node
        else:
            self.head.prev = node
        self.head = node
        self.size += 1

    def insert_back(self, data):
        node = Node(data)
        node.owner = self
        node.prev = self.tail
        if self.tail is None:
            self.head = node
        else:
            self.tail.next = node
        self.tail = node
        self.size += 1
        return node

    def remove_node(self, node):
        if node.owner is not self:
            raise ValueError("node does not belong to this list")
        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next
        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev
        node.prev = None
        node.next = None
        node.owner = None
        self.size -= 1
        return node.data

    def remove_front(self):
        return None if self.head is None else self.remove_node(self.head)

    def remove_back(self):
        return None if self.tail is None else self.remove_node(self.tail)

    def move_to_front(self, node):
        if node.owner is not self:
            raise ValueError("node does not belong to this list")
        if node is not self.head:
            self.remove_node(node)
            self._attach_front(node)
