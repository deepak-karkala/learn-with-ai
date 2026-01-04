# Web Crawler

Welcome to our system design tutorial on building a Web Crawler. A web crawler, also known as a spider or a bot, is a fundamental component of the internet, powering search engines and data aggregation platforms. We'll design a system that can systematically browse the World Wide Web, fetch content, and store it for later processing.

### 1. Problem Statement

We need to design a service that automatically discovers and downloads web pages from the internet. This service will start with an initial list of URLs (called seed URLs) and progressively follow hyperlinks on those pages to find and fetch new pages. The primary output of this process is the collected web page data, which will serve as input for other systems like a search engine indexer.

#### 1a. Follow-up Questions to Ask

To refine our design, we should first clarify the scope with some key questions:

*   **Scale:** How many web pages are we expected to crawl in total? How many pages does an average website have? (e.g., 5 billion pages total)
*   **Data Size:** What is the average size of a web page we will be downloading? (e.g., 2 MB of content)
*   **Freshness:** How often do we need to re-crawl pages to keep our data up-to-date? (This will vary based on page type, from minutes for news sites to weeks for static pages).

### 2. Functional and Non-functional Requirements

#### Functional Requirements
*   **Crawling:** The system must be able to crawl HTML files from the web, starting from a given set of seed URLs.
*   **URL Extraction:** The system must parse downloaded HTML pages to extract new URLs to crawl.
*   **Storage:** It must store the content of crawled pages in a durable blob store.
*   **Scheduling:** The system needs a recurring schedule to re-crawl pages and keep the content fresh.
*   **Politeness:** The crawler must respect the `robots.txt` file of websites, which outlines the rules for bots.

#### Non-Functional Requirements
*   **Scalability:** The system must be highly scalable, distributed, and multithreaded to handle the vastness of the web.
*   **Extensibility:** The design should be modular, allowing for easy extension to support new protocols (like FTP) and file types (images, videos).
*   **Consistency:** All distributed crawler workers must adhere to a common set of rules to ensure the crawled data is consistent.
*   **Performance:** The system should have high throughput (URLs crawled per second) and be self-throttling to avoid overwhelming any single web server.

### 3. Capacity Planning

Let's perform some back-of-the-envelope calculations to understand the scale we're dealing with.

*   **Target:** Crawl 5 billion web pages.

#### Storage Estimation
*   Average page content size: 2 MB
*   Metadata per page (URL, crawl time, etc.): 500 Bytes
*   Total Storage: `5 billion pages * (2 MB + 500 B) ≈` **10 PB**.

#### Server Estimation
*   Average time to download one page (including network latency): 60 ms
*   Time for one server to crawl all 5 billion pages: `5,000,000,000 * 60 ms ≈ 9.5 years`.
*   To crawl all pages in **1 day**, we would need `9.5 * 365 ≈ 3467` servers running a single thread.
*   Assuming each server can run 10 concurrent crawler threads, we would need approximately **350-400 servers**.

#### Bandwidth Estimation
*   Total data to download per day: 10 PB
*   Required Bandwidth: `10 PB / 86400 seconds ≈ 115 GB/s ≈` **920 Gbps**.
*   If we use 400 servers, the bandwidth required per server is `920 Gbps / 400 ≈ 2.3 Gbps`.

### 4. API Design

A web crawler is primarily a backend data processing pipeline. It doesn't typically have a public-facing API for end-users like a search engine does. The main "inputs" are the seed URLs and user-defined crawling jobs. Communication between the internal microservices will be handled via **Remote Procedure Calls (RPC)** for better performance and lower latency compared to REST over HTTP.

### 5. Data Modelling

Our system will rely on several key data stores:

1.  **URL Frontier (Priority Queue):** This is the heart of the scheduler, managing the list of URLs to be crawled. Each entry contains the URL, its priority, and its re-crawl frequency. This can be implemented using a scalable message queue.
2.  **URL Metadata Store (Relational Database):** A database like PostgreSQL would store metadata for every URL seen, including its priority, update frequency, last crawl time, and the checksum of its content.
3.  **Content Store (Blob Storage):** Since web pages contain large, unstructured data (HTML, text, images), a distributed blob store like Amazon S3 or HDFS is the ideal choice for storing the downloaded content.
4.  **Checksum Stores (Key-Value Store):** Fast key-value stores like Redis or DynamoDB are used to store the checksums of URLs and documents to quickly detect duplicates.

### 6. High-Level Architecture

The crawling process can be broken down into a pipeline of specialized services that work together.

<img src="../../_static/system_design/web_crawler/overall_system.png" alt="High-Level Architecture of a Web Crawler" width="800"/>
<br/>
<small>Source: Educative.io: Web Crawler</small>

Here is the step-by-step workflow:

1.  **Scheduler / URL Frontier:** The process begins here. The Frontier provides a list of URLs to the crawler workers. It prioritizes URLs (e.g., high-priority news sites vs. low-priority forums).
2.  **Crawler Workers (Service Host):** These are the workhorses of the system. A worker gets a URL from the scheduler.
3.  **DNS Resolver:** The worker resolves the URL's hostname to an IP address. A custom, cached DNS resolver is used to speed up this frequent operation.
4.  **HTML Fetcher:** Using the IP address, the fetcher downloads the page's content. A critical first step is to fetch and respect the site's `robots.txt` file.
5.  **Extractor:** The worker then passes the downloaded content to the Extractor, which parses the HTML to extract two key things: the page's text content and any new hyperlinks.
6.  **Duplicate Eliminator:**
    *   The extracted **content** is hashed, and its hash is checked against a database of known content to avoid storing duplicates. If unique, the content is saved to the **Blob Store**.
    *   The extracted **URLs** are normalized (e.g., converting to lowercase, adding trailing slashes) and checked against a database of already-seen URLs to avoid re-adding them to the frontier.
7.  **URL Frontier (Update):** Unique, new URLs are sent back to the URL Frontier to be scheduled for future crawling.

---
**🧠 Quiz Time!**

1.  What is the purpose of the `robots.txt` file?
2.  Why is a blob store a better choice for storing webpage content than a relational database?

*(Answers at the end of the tutorial)*
---

### 7. Deep Dive into Core System Components

#### Scheduler (URL Frontier)
This component decides which page to crawl next. It's essentially a large-scale, distributed priority queue.
*   **Prioritization:** News websites might be given high priority and scheduled for re-crawling every few minutes, while a static blog post might have a low priority and be re-crawled every few weeks.
*   **Distribution:** To scale, we can't use a single centralized queue. A common strategy is to distribute URLs based on their hostname. A consistent hashing of the hostname determines which worker (and its local sub-queue) is responsible for that domain. This ensures **politeness**, as all requests to a single website come from a single worker, making it easier to manage request rates.

#### HTML Fetcher
This service is responsible for the actual downloading of content.
*   **User-Agent:** It must identify itself with a `User-Agent` header (e.g., `MyAwesomeCrawler/1.0`), which is a common practice.
*   **Dynamic Content:** Modern websites often use JavaScript to render content. The fetcher may need to include a headless browser (like Puppeteer) to perform server-side rendering to get the full page content.
*   **Sitemaps:** Many websites provide a `sitemap.xml` file, which lists all crawlable URLs on the site. The fetcher can use this as a shortcut to discover pages more efficiently.

#### Extractor
After content is fetched, the extractor parses it.
*   **URL Normalization:** Links can appear in many forms (`example.com`, `http://www.example.com`, `EXAMPLE.COM/page/`). Before being processed, all URLs must be converted to a canonical (standard) form to prevent the same page from being treated as multiple different URLs.
*   **Extensibility:** The extractor can be designed to handle more than just text. Using libraries like **Apache Tika**, it can identify and parse various document formats like PDFs, Word documents, images, and videos.

#### Duplicate Eliminator
The web is full of duplicate content. To save storage and processing time, we must detect and discard duplicates.
*   **URL Duplicates:** A Bloom filter is an excellent probabilistic data structure for quickly checking if a URL has already been seen and added to the frontier. It's fast and memory-efficient.
*   **Content Duplicates:** Simply hashing a document (e.g., with SHA-256) is brittle; a one-byte change results in a completely different hash. More advanced techniques are needed:
    *   **Simhash:** A locality-sensitive hashing algorithm used by Google. It produces hashes where similar documents have similar hash values, allowing for the detection of near-duplicate pages.
    *   **MinHash:** Used to estimate the similarity between two sets (e.g., the set of words in two documents).

### 8. Bottlenecks, Performance, Scalability, and Fault Tolerance

#### Crawler Traps
A major performance risk is "crawler traps"—parts of a website designed (intentionally or not) to cause a crawler to make infinite requests, such as a calendar with endless "next month" links.
*   **Solution:** Be intelligent. The crawler should set limits on how deep it will go into a specific directory or how many URLs with similar patterns it will crawl from a single domain. Respecting `Disallow` rules in `robots.txt` also helps avoid many common traps.

#### Fault Tolerance
*   **Checkpointing:** Stateful services, like the workers managing their queues, should periodically save their state (checkpoint) to durable storage like Amazon S3. If a worker crashes, a new one can start from the last saved checkpoint, minimizing lost work.
*   **Dead-Letter Queues:** If a service consistently fails to process a message (e.g., a malformed URL), the message should be moved to a dead-letter queue after several retries. This prevents a single bad message from halting the entire pipeline.

#### Performance & Scalability
*   **Geographic Distribution:** Deploy crawler workers in data centers around the world. A worker in Europe will have lower latency when crawling European websites.
*   **Consistent Hashing:** As mentioned, using consistent hashing to distribute hostnames among workers makes it easy to add or remove servers from the crawler fleet without a massive reshuffling of responsibilities.

---
**🧠 Quiz Time!**

3.  What is a "crawler trap," and how can a crawler avoid one?
4.  Why is consistent hashing useful for assigning domains to crawler workers?

*(Answers at the end of the tutorial)*
---

### 9. Advanced Section

#### Advanced URL Frontier: Balancing Priority and Politeness

A simple priority queue isn't enough. We need to crawl high-priority URLs often, but we must also be polite and not hit the same server too frequently. A sophisticated frontier design addresses this:

<img src="../../_static/system_design/web_crawler/priority_politeness.png" alt="Advanced URL Frontier Design" width="700"/>
<br/>
<small>Source: Tech Dummies Narendra L: web crawler</small>

1.  **Front Queues:** We have multiple queues, each corresponding to a different priority level. A scheduler selects from these queues based on priority (e.g., taking 5 URLs from P1, 3 from P2, 1 from P3).
2.  **Back Queues:** The selected URLs are routed to back-end queues. Each back queue is dedicated to a **single hostname**. This ensures all URLs for `example.com` are in one queue.
3.  **Min-Heap:** A min-heap tracks the next available crawl time for each back queue (hostname). A worker thread asks the heap for the next ready item. The heap returns the queue whose host is ready to be crawled (i.e., its "earliest next crawl time" is in the past).
4.  **Update Loop:** After a worker fetches a URL from a back queue (e.g., for `cnn.com`), that queue's entry in the min-heap is updated with a new timestamp: `current_time + politeness_delay`. This prevents any URL from `cnn.com` being crawled again until the delay has passed.

#### Detecting Content Updates Efficiently
Re-downloading a 2 MB page just to check if it has changed is wasteful.
*   **Solution:** Use the **HTTP HEAD** request. A HEAD request is identical to a GET request, but the server does not return the message body. The response headers, however, include metadata like `Last-Modified` and `Content-Length`. Our crawler can store these values from the previous crawl and issue a HEAD request first. If the headers haven't changed, there is no need to issue a full GET request to re-download the content.

#### Handling IP Blocks
For a real-time news platform, frequent re-crawls are necessary but can lead to the crawler's IP address being blocked.
*   **Strategies:**
    *   **Large Pool of Proxies:** Use a large, rotating pool of IP addresses from different geographic regions.
    *   **Adaptive Crawl Rate:** Monitor the response codes from a server. If you start receiving `429 (Too Many Requests)` or `503 (Service Unavailable)` errors, automatically slow down the crawl rate for that domain.
    *   **Distributed Crawling:** Ensure requests to a single domain come from a wide range of IPs, not just one worker's address.

***

### Quiz Answers

1.  The `robots.txt` file is a standard used by websites to communicate with web crawlers, indicating which parts of the site should not be processed or scanned.
2.  A blob store is designed for large, unstructured data, which is exactly what web content is. It is more scalable and cost-effective for this use case than a relational database, which is optimized for structured data and transactional queries.
3.  A "crawler trap" is a part of a website that causes a crawler to make a seemingly infinite number of requests (e.g., an endless calendar). A crawler can avoid this by setting limits on crawl depth per directory and respecting the `robots.txt` file.
4.  Consistent hashing allows for the easy addition or removal of crawler servers. When a new server is added, only a small fraction of the domains need to be reassigned, avoiding a complete rebalancing of the workload.