# Low-Level Design: Pub-Sub System

## 1. Requirements (~5 minutes)

### Functional Requirements

1. Publishers can publish messages to a topic.
2. Subscribers can subscribe to topics.
3. All subscribers of a topic receive published messages.
4. Subscribers can unsubscribe from topics.
5. Invalid topics or messages should be handled gracefully.

### Out of Scope

- Distributed broker infrastructure
- Message persistence
- Retries and dead-letter queues
- Concurrency and thread safety

---

## 2. Entities and Relationships (~3 minutes)

| Entity | Responsibility |
|---|---|
| `PubSubBroker` | Coordinates topics, publishing, and subscriptions. |
| `Topic` | Maintains subscribers registered for a topic and notifies them. |
| `Publisher` | Publishes messages through the broker. |
| `Subscriber` | Receives and processes messages. |
| `Message` | Encapsulates event data. |

### Relationships

- `PubSubBroker` manages multiple `Topic` objects.
- `Topic` maintains multiple `Subscriber` references.
- `Publisher` uses `PubSubBroker` to publish messages.
- `Topic` invokes the `Subscriber` interface to deliver messages.

### Message Flow

```text
Publisher
    |
    v
PubSubBroker
    |
    v
Topic
    |
    +----> Subscriber A
    +----> Subscriber B
    +----> Subscriber C
```

---

## 3. Class Design (~10–15 minutes)

### 3.1. Message

**Purpose:** Represents the event data being published.

**State:**
- `id: String` — uniquely identifies the message.
- `payload: Object` — contains the event data.
- `timestamp: DateTime` — records when the message was created.

**OOP Concept: Encapsulation**

Groups related message data into a single object.

### 3.2. Subscriber (Interface)

**Purpose:** Defines a common contract for all message consumers.

**Methods:**
- `onMessage(message: Message): void` — processes a received message.

**OOP Concepts:**
- **Abstraction:** Exposes a common message-handling contract.
- **Polymorphism:** Different subscriber implementations can process the same message differently.

### 3.3. Topic

**Purpose:** Manages subscriber registrations and notifies subscribers when a message arrives.

**State:**
- `name: String` — identifies the topic.
- `subscribers: List<Subscriber>` — stores registered subscribers.

**Methods:**
- `addSubscriber(subscriber)` — registers a subscriber.
- `removeSubscriber(subscriber)` — unregisters a subscriber.
- `notifySubscribers(message)` — invokes `onMessage()` for each registered subscriber.

**Design Patterns and Principles:**
- **Observer Pattern:** Notifies registered subscribers when an event occurs.
- **Encapsulation:** Manages the subscriber list internally.
- **Dependency Inversion Principle (DIP):** Depends on the `Subscriber` abstraction rather than concrete subscriber classes.

### 3.4. PubSubBroker

**Purpose:** Acts as the central coordinator for topics, subscriptions, and publishing.

**State:**
- `topics: Map<String, Topic>` — maps topic names to their corresponding topic objects.

**Methods:**
- `createTopic(name)` — creates and registers a topic.
- `subscribe(topicName, subscriber)` — finds the topic and registers the subscriber.
- `unsubscribe(topicName, subscriber)` — finds the topic and removes the subscriber.
- `publish(topicName, message)` — finds the topic and delegates message notification to it.

**Design Principles:**
- **Single Responsibility Principle (SRP):** Coordinates topic-related operations without implementing subscriber-specific processing.
- **Facade-like role:** Provides a simple API for publishing and subscription management.

### 3.5. Publisher

**Purpose:** Publishes messages without knowing which subscribers will receive them.

**Methods:**
- `publish(topicName, message, broker)` — delegates message publishing to the broker.

**Design Principles:**
- **Loose Coupling:** The publisher does not depend on concrete subscriber implementations.
- **Single Responsibility Principle (SRP):** Publishes events without managing subscriptions.

---

## 4. OOP Concepts, Design Principles, and Patterns

| Concept / Principle / Pattern | Application |
|---|---|
| Encapsulation | `Topic` manages its subscriber list internally. |
| Abstraction | `Subscriber` defines the `onMessage()` contract. |
| Polymorphism | Different subscriber implementations process messages differently. |
| Composition | The broker manages topics, and topics maintain subscriber references. |
| Observer Pattern | A topic notifies its registered subscribers when a message is published. |
| Dependency Inversion Principle | `Topic` depends on the `Subscriber` interface, not concrete implementations. |
| Open/Closed Principle (OCP) | New subscriber types can be added without changing topic notification logic. |
| Single Responsibility Principle (SRP) | Each class has a distinct responsibility. |

---

## 5. Interview Delivery Flow

1. **Requirements:** Clarify publishing, subscribing, unsubscribing, and delivery behavior.
2. **Entities:** Identify `PubSubBroker`, `Topic`, `Publisher`, `Subscriber`, and `Message`.
3. **Message:** Define the structure of the event being passed.
4. **Subscriber Interface:** Establish abstraction and polymorphism.
5. **Topic:** Implement subscriber registration and notification using the Observer pattern.
6. **PubSubBroker:** Coordinate topic operations while maintaining separation of responsibilities.
7. **Publisher:** Delegate publishing to the broker to maintain loose coupling.

---

## Key Interview Takeaway

The Pub-Sub system uses the **Observer Pattern** for topic-based notifications, **interfaces and polymorphism** for extensibility, and the **Dependency Inversion Principle** to decouple topics from concrete subscribers.

The broker separates publishers from subscribers, allowing new subscriber types to be introduced without modifying the publisher.
