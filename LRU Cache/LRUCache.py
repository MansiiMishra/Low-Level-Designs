class Node:
    def __init__(self, key, value):
        # Store the key and value, plus links to the neighboring nodes.
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:

    # Start with an empty doubly linked list between head and tail sentinels.
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.head = Node(-1, -1)
        self.tail = Node(-1, -1)
        self.head.next = self.tail
        self.tail.prev = self.head

    def remove(self, node):
        # Join the nodes around this one, unlinking it from the list.
        node.prev.next = node.next
        node.next.prev = node.prev

    def addtohead(self, node):
        # Put this node first, making it the most recently used.
        node.prev = self.head
        node.next = self.head.next
        # The old first node now follows this node.
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        # Return -1 if missing; otherwise mark the item as most recently used.
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self.remove(node)
        self.addtohead(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        # Update an existing item and mark it as most recently used.
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self.remove(node)
            self.addtohead(node)
            return
        # If full, remove the least recently used item at the tail end.
        if len(self.cache) >= self.capacity:
            lru_node = self.tail.prev
            self.remove(lru_node)
            del self.cache[lru_node.key]

        # Add a new item at the front and record it for quick lookup.
        node = Node(key, value)
        self.addtohead(node)
        self.cache[key] = node