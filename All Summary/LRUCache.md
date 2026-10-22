# LRU Cache — Low-Level Design

## 1. Problem Statement

Design an **LRU (Least Recently Used) Cache** that supports two operations:

- `get(key)`: Return the value associated with the key, or `-1` if the key does not exist.
- `put(key, value)`: Insert a new key-value pair or update an existing key.

When the cache exceeds its capacity, evict the **least recently used** entry.

## 2. Data Structures

We use two data structures:

| Data Structure | Purpose | Time Complexity |
|---|---|---|
| HashMap (`cache`) | Maps each key to its corresponding DLL node | O(1) average |
| Doubly Linked List (DLL) | Maintains usage order | O(1) for insertion/removal |

The DLL uses two sentinel nodes:

- `head`: The most recently used node is immediately after it.
- `tail`: The least recently used node is immediately before it.

**Ordering:** `head → Most Recently Used → ... → Least Recently Used → tail`

## 3. Class Design

### `Node`

Represents one cache entry.

**State**
- `key`: Cache key.
- `value`: Value associated with the key.
- `prev`: Reference to the previous node.
- `next`: Reference to the next node.

**Purpose:** Stores an entry and its position in the doubly linked list.

### `LRUCache`

Manages the cache operations and eviction policy.

**State**
- `capacity`: Maximum number of entries.
- `cache`: HashMap mapping keys to node references.
- `head`: Sentinel node at the beginning of the DLL.
- `tail`: Sentinel node at the end of the DLL.

**Methods**

| Method | Purpose |
|---|---|
| `__init__(capacity)` | Initializes the HashMap and sentinel nodes |
| `remove(node)` | Detaches a node from the DLL |
| `addtohead(node)` | Inserts a node at the front, marking it most recently used |
| `get(key)` | Retrieves a value and updates usage order |
| `put(key, value)` | Inserts or updates an entry and evicts if necessary |

## 4. Implementation

```python
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}

        self.head = Node(-1, -1)
        self.tail = Node(-1, -1)

        self.head.next = self.tail
        self.tail.prev = self.head

    def remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def addtohead(self, node):
        node.prev = self.head
        node.next = self.head.next

        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1

        node = self.cache[key]

        self.remove(node)
        self.addtohead(node)

        return node.value

    def put(self, key: int, value: int) -> None:
        # Case 1: Key already exists.
        if key in self.cache:
            node = self.cache[key]
            node.value = value

            self.remove(node)
            self.addtohead(node)
            return

        # Case 2: New key; evict LRU entry if full.
        if len(self.cache) >= self.capacity:
            lru_node = self.tail.prev

            self.remove(lru_node)
            del self.cache[lru_node.key]

        # Insert the new entry.
        node = Node(key, value)
        self.addtohead(node)
        self.cache[key] = node
```

## 5. Workflow and Algorithms

### GET Operation

1. Check whether the key exists in the HashMap.
2. If missing, return `-1`.
3. Otherwise, retrieve the corresponding node.
4. Remove it from its current position in the DLL.
5. Insert it immediately after `head`.
6. Return the node's value.

**Why?** Accessing an entry makes it the most recently used.

### PUT Operation

**Case 1: Key already exists**

1. Find its node using the HashMap.
2. Update the node's value.
3. Move the node to the head.
4. Return.

**Case 2: Key does not exist**

1. Check whether the cache is at capacity.
2. If full, remove `tail.prev`, the least recently used node.
3. Delete the evicted key from the HashMap.
4. Create a new node.
5. Insert it immediately after `head`.
6. Add the key-to-node reference to the HashMap.

## 6. Example Walkthrough

Assume the cache has capacity `2`.

| Operation | Cache order (MRU → LRU) | Result |
|---|---|---|
| `put(1, 1)` | `1` | — |
| `put(2, 2)` | `2 → 1` | — |
| `get(1)` | `1 → 2` | `1` |
| `put(3, 3)` | `3 → 1` | Evicts key `2` |
| `get(2)` | `3 → 1` | `-1` |
| `put(4, 4)` | `4 → 3` | Evicts key `1` |
| `get(1)` | `4 → 3` | `-1` |
| `get(3)` | `3 → 4` | `3` |
| `get(4)` | `4 → 3` | `4` |

## 7. Test Class

Save the implementation in `LRUCache.py` and the following test in `test_lru_cache.py`.

```python
from LRUCache import LRUCache


class TestLRUCache:
    def test(self):
        lruCache = LRUCache(2)

        lruCache.put(1, 1)
        lruCache.put(2, 2)
        assert lruCache.get(1) == 1

        lruCache.put(3, 3)
        assert lruCache.get(2) == -1

        lruCache.put(4, 4)
        assert lruCache.get(1) == -1

        assert lruCache.get(3) == 3
        assert lruCache.get(4) == 4


def test_lru_cache():
    TestLRUCache().test()
```

Run the tests with:

```bash
pytest -v test_lru_cache.py
```

Using `assert` makes the test fail automatically if an operation returns an unexpected value.

## 8. Edge Cases

- **Missing key:** `get()` returns `-1`.
- **Updating an existing key:** Update the value without increasing cache size.
- **Capacity of one:** Inserting a different key evicts the previous entry.
- **Repeated access:** Each successful `get()` moves the node to the head.
- **Eviction:** Always remove `tail.prev`.
- **Capacity of zero:** The current implementation does not support this case; `put()` would attempt to evict a sentinel node. Validate that capacity is positive in the constructor, or explicitly define zero-capacity behavior.

## 9. Time and Space Complexity

| Operation | Complexity |
|---|---|
| `get()` | O(1) average |
| `put()` | O(1) average |
| `remove()` | O(1) |
| `addtohead()` | O(1) |
| Space | O(capacity) |

The HashMap provides fast node lookup, while the DLL provides fast insertion, removal, and eviction.

## 10. OOP Concepts and Design Decisions

- **Encapsulation:** `LRUCache` manages the cache state and exposes `get()` and `put()` as its primary operations.
- **Composition:** `LRUCache` contains a HashMap and DLL nodes.
- **Sentinel nodes:** Avoid special-case logic when inserting or removing the first or last real node.
- **Separation of responsibilities:** `Node` stores entry data; `LRUCache` manages lookup, ordering, and eviction.

## 11. Final Class Design

```text
LRUCache
 ├── capacity: int
 ├── cache: HashMap<Key, Node>
 ├── head: Node
 ├── tail: Node
 │
 ├── get(key)
 ├── put(key, value)
 ├── remove(node)
 └── addtohead(node)

Node
 ├── key
 ├── value
 ├── prev: Node
 └── next: Node
```

**Key interview takeaway:** The HashMap alone cannot efficiently track which entry was used least recently. Combining a HashMap with a doubly linked list gives average O(1) lookup, updates, recency changes, and eviction.
