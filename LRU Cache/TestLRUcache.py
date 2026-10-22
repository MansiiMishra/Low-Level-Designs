from LRUCache import LRUCache

class TestLRUCache:
    def test(self):
        lruCache = LRUCache(2)

        lruCache.put(1, 1)
        lruCache.put(2, 2)
        print(lruCache.get(1))  # 1

        lruCache.put(3, 3)      # Evicts key 2
        print(lruCache.get(2))  # -1

        lruCache.put(4, 4)      # Evicts key 1
        print(lruCache.get(1))  # -1

        print(lruCache.get(3))  # 3
        print(lruCache.get(4))  # 4


# Run the test
test = TestLRUCache()
test.test()