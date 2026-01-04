# System Design Tutorial: The URL Shortener

Welcome to this system design tutorial where we'll break down how to build a scalable URL shortening service like TinyURL or Bitly. We will start with the basic requirements and progressively build up to a robust, scalable, and fault-tolerant system.

### 1. Problem Statement

The goal is to design a URL shortening service that takes a long URL as input and returns a much shorter, unique URL. When a user accesses the short URL, they should be seamlessly redirected to the original long URL.

#### 1a. Follow-up Questions to Ask

Before diving into the design, it's crucial to clarify the scope and expectations. Here are some excellent questions to ask the interviewer:

*   **Use Cases:** What are the primary features? (e.g., just shortening and redirection, or also custom URLs and analytics?)
*   **Traffic Volume (Writes):** How many new URLs will be shortened per day? (e.g., 100 million Daily Active Users for writes)
*   **Traffic Volume (Reads):** What is the anticipated read-to-write ratio? (e.g., 100:1)
*   **Data Persistence:** How long should a generated short URL remain active? (e.g., 5 years)
*   **URL Characteristics:** What is the maximum acceptable length for a short URL? (e.g., 9 characters)
*   **Usage Pattern:** Will shortened URLs be accessed frequently or just once or twice? (e.g., most are accessed only once after creation)
*   **Users:** Who will be using the service? (e.g., the general public)

### 2. Functional and Non-functional Requirements

Based on the problem statement, we can define the system's requirements.

#### Functional Requirements
*   **Shorten URL:** Given a long URL, the system must generate a unique, readable, and non-predictable short URL.
*   **Redirection:** When a user accesses a short URL, the system must redirect them to the corresponding long URL.
*   **Custom URL:** Users should be able to choose a custom short URL.
*   **Expiration:** Users should be able to set an expiration time for their short URLs.
*   **Analytics:** The system should support tracking metrics like the number of clicks for a short URL.

#### Non-Functional Requirements
*   **High Availability:** The system must be operational and accessible at all times.
*   **Low Latency:** Both URL shortening and redirection should be extremely fast.
*   **Scalability:** The system must handle a massive increase in traffic and data.
*   **Durability & Fault Tolerance:** The system should not lose data, even if components fail.

### 3. Capacity Planning

Let's estimate the scale of our system based on the clarified requirements. This helps in making informed decisions about technology choices and architecture.

*   **Write Traffic:** 100 million new URLs per day.
    *   Queries Per Second (QPS) for writes: `100,000,000 / (24 * 3600) ≈ 1160 QPS` (let's round to **1000 QPS**).
*   **Read Traffic:** Read:Write ratio is 100:1.
    *   QPS for reads: `1000 QPS (write) * 100 =` **100,000 QPS**.
*   **Conclusion:** The system is heavily **read-heavy**.

#### Storage Estimation

Let's assume a record in our database has the following fields:
*   `long_url`: 500 bytes
*   `short_url`: 20 bytes
*   `user_id`: 20 bytes
*   `created_at`: 10 bytes
*   `expires_at`: 10 bytes
*   `last_visited`: 10 bytes
*   **Total per record:** ~570 bytes (let's use 2.5 KB for a more conservative estimate including overhead).

Total storage for 5 years:
*   `100,000,000 (URLs/day) * 365 (days/year) * 5 (years) * 2.5 KB/URL ≈` **456 TB**.
*   With a replication factor of 3 for durability, the total storage needed is `456 * 3 ≈` **1.37 PB**.

#### Bandwidth Estimation
*   **Ingress (Writes):** `1000 requests/sec * 2.5 KB/request ≈` **2.5 MB/sec**.
*   **Egress (Reads):** `100,000 requests/sec * 2.5 KB/request ≈` **250 MB/sec**.

---
**🧠 Quiz Time!**

1.  Based on the capacity planning, which operation (read or write) is the primary target for performance optimization?
2.  Why is it important to have a replication factor for storage?

*(Answers at the end of the tutorial)*
---

### 4. API Design

A RESTful API is a standard choice for public-facing services due to its simplicity and loose coupling.

#### 1. Shorten a URL

The client sends the long URL and other optional parameters to the server. We use the `PUT` method because it is idempotent; sending the same request multiple times will produce the same result (the same short URL for the same long URL), which aligns with our requirements.

**Request:** `PUT /url`
```json
{
    "long_url": "https://en.wikipedia.org/wiki/URL_shortening",
    "tags": ["productivity"],
    "expires": "2028-08-15T20:00:00Z",
    "custom": "wiki-short"
}
```

**Success Response:** `200 OK`
```json
{
    "long_url": "https://en.wikipedia.org/wiki/URL_shortening",
    "short_url": "http://short.ly/wiki-short",
    "created_at": "2025-08-15T13:00:00Z",
    "is_active": true
}
```
Other potential status codes include `401 Unauthorized` (invalid credentials) or `403 Forbidden` (insufficient privileges).

#### 2. Redirect a Short URL

The client makes a simple GET request to the short URL.

**Request:** `GET /:short-url`

**Success Response:** `301 Moved Permanently`
```
status code: 301 Moved Permanently
location: <long-url>
cache-control: public, expires=datetime
```
*   **Why `301`?** A `301` status code indicates a permanent move. This is SEO-friendly and allows browsers to cache the redirect. However, for analytics, we need to be careful. If the browser caches the redirect, subsequent requests won't hit our server, and we can't collect data. The `cache-control` header can be used to manage this, allowing caching on public caches (like a CDN) but not on the client's private browser cache.
*   **Other options:**
    *   `302 Found`: A temporary redirect. Not ideal for SEO.
    *   `307 Temporary Redirect`: A temporary redirect that preserves the original request's HTTP method (e.g., a `PUT` remains a `PUT`).

**Failure Response:** `404 Not Found`
If the short URL does not exist in the database, the server returns a `404` status code.

### 5. Data Modelling

Our data storage needs to be fast and scalable. Given the massive scale and the simple key-value nature of our primary data (mapping a short URL to a long URL), a NoSQL database is an excellent fit.

#### Database Schema
We can split our data into two main tables: `Users` and `URL`.

*   **Users Table:** This contains user information. Since this data is structured and relational (users have URLs), a **SQL database** like PostgreSQL or MySQL is a good choice. It offers ACID compliance and is efficient for indexed lookups.
*   **URL Table:** This stores the mapping between short and long URLs. This table will be massive and read-heavy. A **NoSQL database** like MongoDB or DynamoDB is ideal due to its horizontal scalability and flexible schema.

Here is a visual representation of the schema:

<img src="../../_static/system_design/url_shortener/schema.png" alt="Database Schema" width="400"/>
<br/>
<small>Source: Neo Kim: URL Shortener</small>

#### Why MongoDB?
MongoDB uses a leader-follower architecture. This is great for our read-heavy system because reads can be distributed across multiple follower replicas, increasing read throughput. Writes go through a single leader, which prevents race conditions and ensures consistency.

### 6. High-Level Architecture

Let's put the components together in a high-level diagram.

<img src="../../_static/system_design/url_shortener/overall_system.png" alt="High-Level Architecture" width="800"/>
<br/>
<small>Source: systemdesign.one: URL Shortener</small>

The flow works as follows:

1.  **Client:** The user interacts with our service via a web browser or mobile app.
2.  **DNS:** The Domain Name System resolves our service's domain name to an IP address of a load balancer.
3.  **Load Balancer:** Distributes incoming client requests across multiple application servers to prevent any single server from being overwhelmed.
4.  **Application Servers:** These are stateless services that handle the core logic.
    *   **Write Path (Shortening):** An application server receives a request to shorten a URL, calls the Short URL Generator, and stores the mapping in the database.
    *   **Read Path (Redirection):** An application server receives a request for a short URL, looks up the long URL in the cache or database, and returns a 301 redirect.
5.  **Short URL Generator (SUG):** A dedicated service responsible for creating unique short IDs.
6.  **Database:** A distributed SQL/NoSQL database cluster to store the data.
7.  **Cache:** An in-memory cache (like Redis or Memcached) sits in front of the database to store frequently accessed URL mappings, reducing latency and database load.

### 7. Deep Dive into Core System Components

#### Short URL Generator (SUG)

This is the heart of our write path. It must generate short, unique, and non-predictable IDs. A common approach involves two components:

1.  **Sequencer:** Generates a unique, 64-bit integer ID. This ID is guaranteed to be unique across the entire system.
2.  **Encoder:** The unique integer ID is then encoded into a more readable format. **Base58** encoding is a great choice. It's similar to Base62 but avoids visually confusing characters like `0` (zero), `O` (capital o), `l` (lowercase L), and `I` (capital i).

A 7-character Base62 string can generate over 3.5 trillion unique URLs, which is more than enough for our needs for many years.

#### Caching Layer
Since our system is 100 times more read-heavy than write-heavy, caching is critical for performance.

*   **Choice of Cache:** **Memcached** is an excellent choice. It's a simple, fast, and horizontally scalable in-memory key-value store.
*   **Caching Strategy:** We use the **cache-aside** pattern.
    1.  When a request for a short URL comes in, the application server first checks the cache.
    2.  **Cache Hit:** If the URL is in the cache, it's returned directly.
    3.  **Cache Miss:** If the URL is not in the cache, the server queries the database, retrieves the long URL, stores it in the cache for future requests, and then returns it to the client.
*   **Eviction Policy:** When the cache is full, we need to evict old data. The **Least Recently Used (LRU)** policy is a perfect fit, as it removes the data that hasn't been accessed for the longest time.

### 8. Bottlenecks, Performance, Scalability, and Fault Tolerance

#### Bottlenecks and Optimizations

*   **Database Hotspots:** A single database can become a bottleneck under heavy load.
    *   **Solution:** **Sharding** (partitioning) the database. We can partition the URL table based on the `short_url`. This distributes the data and load across multiple database servers.
*   **Single Point of Failure (SPOF):** Any single component (load balancer, database leader) could fail.
    *   **Solution:** **Replication and Redundancy**. Have multiple load balancers in an active-passive setup. Replicate database servers so that if a leader fails, a follower can be promoted to take its place.
*   **Slow Writes Under Load:** If the database slows down during traffic spikes:
    *   **Short-term:** Vertically scale the database server (add more CPU/RAM).
    *   **Long-term:** Horizontally scale by adding more shards. Separate the read and write traffic into different database replicas (Read Replicas).

#### Designing for Scalability
*   **Stateless Services:** The application servers should be stateless. This means they don't store any session data locally. Any server can handle any request, which makes it easy to add or remove servers based on load.
*   **Horizontal Scaling:** Design all components—application servers, databases, caches—to be horizontally scalable. This means adding more machines to handle increased load, which is more cost-effective and flexible than vertical scaling (making a single machine more powerful).

#### Designing for Fault Tolerance
*   **Microservices Architecture:** Break the system down into smaller, independent services (e.g., Shortening Service, Redirection Service, Analytics Service). If one service fails, it doesn't bring down the entire application.
*   **Message Queues:** Use a message queue like **Apache Kafka** to decouple services. For example, when a URL is clicked, the application server can send a message to a Kafka topic. A separate analytics service can then consume these messages asynchronously to process analytics. This prevents the analytics workload from slowing down the critical redirection path.

---
**🧠 Quiz Time!**

3.  What is the main benefit of using a Base58 encoding scheme over Base62?
4.  Explain the "cache-aside" pattern in one sentence.

*(Answers at the end of the tutorial)*
---

### 9. Advanced Section

This section covers more complex topics for building a truly production-grade system.

#### Advanced ID Generation Strategies

The simple sequencer-encoder model works but can be predictable. Here are alternatives:

*   **Twitter Snowflake:** A service that generates 64-bit unique IDs composed of a timestamp, data center ID, worker ID, and a sequence number. This guarantees uniqueness and sortability by time but can be predictable.
*   **Token Range Service:** A central service (managed by a coordination service like **Apache ZooKeeper**) assigns non-overlapping ranges of unique IDs to each instance of the Short URL Generator. This avoids contention but makes the token range service a potential bottleneck.
*   **Hashing:** Hash the long URL (using a function like MD5) and take the first `n` characters.
    *   **Challenge:** Hash collisions are possible (different long URLs producing the same hash). The system must have a strategy to handle collisions, such as appending random characters until a unique short URL is found.

#### Write Path: Handling Duplicate Long URLs

What if a user tries to shorten a long URL that's already in our system? We should return the existing short URL. Querying the database for the long URL before every write is expensive.

*   **Solution:** Use a **Bloom Filter**. A Bloom filter is a probabilistic data structure that can quickly tell you if an item *might* be in a set or is *definitively not* in the set.
    1.  Before writing, check the Bloom filter for the long URL.
    2.  If the filter says "no," the URL is not in the DB. Proceed to create a new short URL.
    3.  If the filter says "yes" (it might be a false positive), then query the database to be certain.
    This dramatically reduces expensive database lookups for new URLs.

#### Read Path: Avoiding Cache Thrashing

A common usage pattern is that a URL is shortened and accessed only once. Caching every single URL on its first access would fill the cache with single-use entries, a phenomenon known as **cache thrashing**.

*   **Solution:** Use another Bloom filter in front of the cache.
    1.  When a URL is accessed for the first time, add it to the Bloom filter but *not* the cache.
    2.  On subsequent requests, check the Bloom filter first. If the URL is present, it means it has been accessed before. Only then should you add it to the main cache.

#### Analytics Pipeline
To handle analytics at scale without impacting performance:
1.  The application server publishes "URL clicked" events to a **Kafka** topic.
2.  A separate batch processing service (like **Apache Spark**) consumes these events, aggregates the data, and stores it in a data warehouse (like **Amazon Redshift** or **Snowflake**) for analysis.

#### Database Cleanup
Expired URLs need to be removed to save space.
*   **Lazy Removal:** When a user requests an expired URL, delete it from the database then. This is simple but doesn't clean up unvisited expired URLs.
*   **Dedicated Cleanup Service:** A background job runs periodically (during off-peak hours) to scan the database and remove expired records.

#### Security
*   **Rate Limiting:** Protect the service from abuse (like DDoS attacks) by limiting the number of requests a user (identified by API key, IP address, or cookie) can make in a given time frame.
*   **Input Sanitization:** Sanitize all user inputs to prevent security vulnerabilities like Cross-Site Scripting (XSS) and SQL Injection.
*   **Authorization:** Use secure tokens like JSON Web Tokens (JWT) to authenticate and authorize API requests.

***

### Quiz Answers

1.  **The read operation.** With a 100:1 read-to-write ratio, optimizing the redirection process will have the largest impact on overall system performance and user experience.
2.  **For durability and fault tolerance.** If the server holding the primary data copy fails, a replica can be used to recover the data, ensuring no data is lost.
3.  **To improve readability and avoid user error.** Base58 removes visually similar characters (like `0` and `O`, `l` and `I`), making the URLs easier for humans to read and type correctly.
4.  The application checks the cache for data; if it's not there (a cache miss), it retrieves the data from the database and then stores a copy in the cache for future requests.