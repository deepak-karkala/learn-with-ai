import { Message } from '@/components/ChatInterface'

// Demo session data for showcasing product features
export const demoSessions = {
  'twitter-clone-demo': {
    id: 'twitter-clone-demo',
    title: 'Design Twitter Clone',
    messages: [
      // Initial conversation
      {
        id: 'msg-1',
        content: 'I want to design a Twitter-like social media platform. Can you help me understand the key components?',
        role: 'user' as const,
        timestamp: new Date('2024-01-15T10:00:00Z'),
        type: 'text' as const
      },
      {
        id: 'msg-2',
        content: `Excellent choice! Twitter is a fascinating system to design. Let's start by breaking down the core functionalities:

**Core Features:**
• User registration and authentication
• Tweet creation and posting (280 character limit)
• Timeline/feed generation
• Following/followers system
• Likes, retweets, and replies
• Real-time notifications
• Search functionality
• Direct messaging

**Key Questions to Consider:**
1. What's our expected scale? (users, tweets per day)
2. How do we handle the massive read-to-write ratio?
3. How do we generate personalized timelines efficiently?

What aspect would you like to dive into first?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:00:30Z'),
        type: 'text' as const
      },
      {
        id: 'msg-3',
        content: 'Let\'s assume we need to support 100 million users with about 500 million tweets per day. I\'m most interested in how we handle the timeline generation and ensure good performance.',
        role: 'user' as const,
        timestamp: new Date('2024-01-15T10:02:00Z'),
        type: 'text' as const
      },
      {
        id: 'msg-4',
        content: `Great scale target! 500M tweets/day means ~5,800 tweets/second average, with much higher peaks. Timeline generation is indeed the heart of Twitter's complexity.

**Timeline Generation Approaches:**

**1. Pull Model (Naive):**
• Query all followed users' tweets on demand
• Sort by timestamp
• ❌ Too slow for large following lists

**2. Push Model (Fan-out on Write):**
• Pre-compute timelines when tweets are posted
• Store in user's timeline cache
• ✅ Fast reads, ❌ expensive for celebrities

**3. Hybrid Model (Twitter's Approach):**
• Push for normal users
• Pull for celebrities
• Merge at read time

For your architecture, I'd recommend the hybrid approach. Would you like to explore the database design for this?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:03:15Z'),
        type: 'text' as const
      },
      // Early assessment
      {
        id: 'msg-5',
        content: '🎯 **Assessment Complete**\n\n**Overall Score:** 2.7/5.0 (Confidence: 4.2/5.0)\n\n**Summary:** Good initial understanding of Twitter\'s core features and scale requirements. Strong grasp of timeline generation challenges.\n\n**Detailed Feedback:** You\'ve correctly identified the key technical challenges of Twitter\'s design. Your understanding of the read-heavy nature and timeline generation complexity is solid. However, we need to dive deeper into the technical implementation details.\n\n**Recommendations:**\n• Explore database schema design in detail\n• Consider caching strategies for hot data\n• Think about geographic distribution and CDN usage\n\n**Next Steps:**\n• Design the complete database schema\n• Sketch the high-level system architecture\n• Consider reliability and fault tolerance mechanisms',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:05:00Z'),
        type: 'text' as const,
        metadata: {
          topic: 'Twitter System Design',
          difficulty: 'intermediate' as const,
          assessment: {
            requirements_analysis: 3,
            system_architecture: 2,
            technical_deep_dive: 3,
            scale_performance: 2,
            reliability_fault_tolerance: 2,
            communication_thought_process: 4
          }
        }
      },
      {
        id: 'msg-6',
        content: 'Yes, let\'s design the database schema. I think we\'ll need tables for users, tweets, followers, and maybe a timeline cache table?',
        role: 'user' as const,
        timestamp: new Date('2024-01-15T10:06:00Z'),
        type: 'text' as const
      },
      {
        id: 'msg-7',
        content: `Excellent thinking! You're on the right track. Let me outline a comprehensive database design:

**Core Tables:**

**Users Table:**
\`\`\`sql
id, username, email, bio, followers_count, following_count, created_at
\`\`\`

**Tweets Table:**
\`\`\`sql
id, user_id, content, timestamp, likes_count, retweets_count, reply_to_id
\`\`\`

**Followers Table:**
\`\`\`sql
follower_id, followee_id, created_at
\`\`\`

**Timeline Cache (Key Innovation):**
\`\`\`sql
user_id, tweet_id, timestamp, tweet_author_id
\`\`\`

**Key Design Decisions:**
• Denormalize counts for performance
• Partition timeline cache by user_id
• Use timestamp-based sharding for tweets
• Consider Redis for hot timeline data

Now, let's visualize the high-level architecture. Can you sketch the main components on the whiteboard?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:07:30Z'),
        type: 'text' as const
      },
      // Whiteboard usage
      {
        id: 'msg-8',
        content: 'Let me create a visual design of the architecture.',
        role: 'user' as const,
        timestamp: new Date('2024-01-15T10:12:00Z'),
        type: 'text' as const
      },
      {
        id: 'msg-8a',
        content: '📋 System Design Whiteboard',
        role: 'user' as const,
        timestamp: new Date('2024-01-15T10:12:15Z'),
        type: 'image' as const,
        imageData: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgdmlld0JveD0iMCAwIDgwMCA2MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNjAwIiBmaWxsPSIjMWYyOTM3Ii8+CjwhLS0gTG9hZCBCYWxhbmNlciAtLT4KPHJlY3QgeD0iMzUwIiB5PSI1MCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzNiODJmNiIgc3Ryb2tlPSIjMjU2M2ViIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSI0MDAiIHk9Ijg1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+TG9hZCBCYWxhbmNlcjwvdGV4dD4KCjwhLS0gV2ViIFNlcnZlcnMgLS0+CjxyZWN0IHg9IjE1MCIgeT0iMjAwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjMjJjNTVlIiBzdHJva2U9IiMxNmEzNGEiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSIyMDAiIHk9IjIzNSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMiIgZm9udC13ZWlnaHQ9ImJvbGQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPldlYiBTZXJ2ZXI8L3RleHQ+Cgo8cmVjdCB4PSIzNTAiIHk9IjIwMCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzIyYzU1ZSIgc3Ryb2tlPSIjMTZhMzRhIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSI0MDAiIHk9IjIzNSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMiIgZm9udC13ZWlnaHQ9ImJvbGQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPldlYiBTZXJ2ZXI8L3RleHQ+Cgo8cmVjdCB4PSI1NTAiIHk9IjIwMCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzIyYzU1ZSIgc3Ryb2tlPSIjMTZhMzRhIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSI2MDAiIHk9IjIzNSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMiIgZm9udC13ZWlnaHQ9ImJvbGQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPldlYiBTZXJ2ZXI8L3RleHQ+Cgo8IS0tIERhdGFiYXNlIC0tPgo8cmVjdCB4PSIxNTAiIHk9IjQwMCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI2MCIgZmlsbD0iI2E4NTVmNyIgc3Ryb2tlPSIjOTMzM2VhIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSIyMDAiIHk9IjQzNSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMiIgZm9udC13ZWlnaHQ9ImJvbGQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkRhdGFiYXNlPC90ZXh0PgoKPCEtLSBSZWRpcyBDYWNoZSAtLT4KPHJlY3QgeD0iNTUwIiB5PSI0MDAiIHdpZHRoPSIxMDAiIGhlaWdodD0iNjAiIGZpbGw9IiNlZjQ0NDQiIHN0cm9rZT0iI2RjMjYyNiIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjYwMCIgeT0iNDM1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+UmVkaXMgQ2FjaGU8L3RleHQ+Cgo8IS0tIENvbm5lY3Rpb25zIC0tPgo8bGluZSB4MT0iNDAwIiB5MT0iMTEwIiB4Mj0iMjAwIiB5Mj0iMjAwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMiIvPgo8bGluZSB4MT0iNDAwIiB5MT0iMTEwIiB4Mj0iNDAwIiB5Mj0iMjAwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMiIvPgo8bGluZSB4MT0iNDAwIiB5MT0iMTEwIiB4Mj0iNjAwIiB5Mj0iMjAwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMiIvPgoKPGxpbmUgeDE9IjIwMCIgeTE9IjI2MCIgeDI9IjIwMCIgeTI9IjQwMCIgc3Ryb2tlPSIjOWNhM2FmIiBzdHJva2Utd2lkdGg9IjIiLz4KPGxpbmUgeDE9IjQwMCIgeTE9IjI2MCIgeDI9IjYwMCIgeTI9IjQwMCIgc3Ryb2tlPSIjOWNhM2FmIiBzdHJva2Utd2lkdGg9IjIiLz4KPC9zdmc+'
      },
      // AI Design Review
      {
        id: 'msg-9',
        content: `Great design! I can see the Twitter architecture you've created. Let me provide some feedback.`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:12:30Z'),
        type: 'text' as const
      },
      {
        id: 'msg-10',
        content: `🎨 **AI Design Review of Your Twitter Architecture:**

**Strengths:**
✅ Good separation of concerns with distinct layers
✅ Load balancer for scalability
✅ Cache layer for performance optimization
✅ Proper database tier separation

**Areas for Improvement:**
🔍 **Missing Components:**
• Message Queue system for async processing
• CDN for static content delivery
• Search service (Elasticsearch)
• Notification service
• Analytics/Metrics collection

🔍 **Architecture Enhancements:**
• Consider microservices split (User Service, Tweet Service, Timeline Service)
• Add database replication (master-slave setup)
• Include monitoring and logging services
• Media storage service for images/videos

**Scalability Considerations:**
• How will you handle database sharding?
• What about geographic distribution for global users?

This design needs refinement for production scale.`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:13:00Z'),
        type: 'text' as const
      },
      {
        id: 'msg-11',
        content: 'Great feedback! Let me address those points. For the message queue, I\'d use Kafka for handling tweet ingestion and notifications. CDN would be CloudFlare for static assets. For search, yes, Elasticsearch cluster. And for microservices, I\'d split into: User Service, Tweet Service, Timeline Service, Notification Service, and Media Service.',
        role: 'user' as const,
        timestamp: new Date('2024-01-15T10:15:00Z'),
        type: 'text' as const
      },
      {
        id: 'msg-12',
        content: `Outstanding improvements! You've addressed all the major concerns with thoughtful solutions:

**Microservices Architecture:**
✅ **User Service:** Authentication, profiles, follow relationships
✅ **Tweet Service:** Tweet CRUD, engagement metrics
✅ **Timeline Service:** Feed generation, caching strategies
✅ **Notification Service:** Real-time alerts, push notifications
✅ **Media Service:** Image/video upload, processing, storage

**Infrastructure Choices:**
✅ **Kafka:** Perfect for high-throughput event streaming
✅ **Elasticsearch:** Excellent for full-text search and analytics
✅ **CloudFlare CDN:** Global edge caching for static content

**Advanced Considerations:**
• **Database Sharding:** User-based or timeline-based?
• **Consistency Models:** Eventual consistency for timeline, strong for financial operations
• **Rate Limiting:** API throttling to prevent abuse
• **Circuit Breakers:** Fault tolerance between services

You've shown excellent understanding of distributed systems principles!`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:16:30Z'),
        type: 'text' as const
      },
      {
        id: 'msg-13',
        content: 'For database sharding, I\'d use user-based sharding for user service and timeline service, but tweet-based sharding by timestamp for the tweet service to handle the time-series nature of tweets. For consistency, eventual consistency for timelines is fine since slight delays are acceptable, but strong consistency for user relationships and tweet counts.',
        role: 'user' as const,
        timestamp: new Date('2024-01-15T10:18:00Z'),
        type: 'text' as const
      },
      // Final assessment
      {
        id: 'msg-14',
        content: '🎯 **Assessment Complete**\n\n**Overall Score:** 4.5/5.0 (Confidence: 4.8/5.0)\n\n**Summary:** Excellent comprehensive design with strong understanding of distributed systems principles. Great improvement from initial assessment.\n\n**Detailed Feedback:** Your final architecture demonstrates production-level thinking with proper microservices decomposition, smart sharding strategies, and well-considered consistency models. The progression from basic to advanced concepts shows strong learning ability.\n\n**Recommendations:**\n• Consider adding more specific details about monitoring and alerting\n• Think about disaster recovery and backup strategies\n• Add details about API rate limiting and security measures\n\n**Next Steps:**\n• Practice implementing one of the microservices in detail\n• Study real-world Twitter engineering blog posts\n• Explore advanced topics like machine learning for feed ranking',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:20:00Z'),
        type: 'text' as const,
        metadata: {
          topic: 'Twitter System Design',
          difficulty: 'intermediate' as const,
          assessment: {
            requirements_analysis: 5,
            system_architecture: 4,
            technical_deep_dive: 5,
            scale_performance: 4,
            reliability_fault_tolerance: 4,
            communication_thought_process: 5
          }
        }
      },
      {
        id: 'msg-15',
        content: `🎉 **Final Summary:**

You've successfully designed a production-ready Twitter clone! Your final architecture shows strong understanding of:

• **Scalability patterns** (sharding, caching, CDN)
• **Microservices design** principles
• **Data consistency** trade-offs
• **Performance optimization** strategies

**Key Strengths:**
• Clear thinking about trade-offs
• Good grasp of distributed systems concepts
• Practical technology choices
• Strong communication of complex ideas

This architecture could handle Twitter-scale traffic with proper implementation. Well done! 🚀`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-15T10:21:00Z'),
        type: 'text' as const
      }
    ]
  },
  'session_2': {
    id: 'session_2',
    title: 'Chat System Architecture',
    messages: [
      {
        id: 'chat-msg-1',
        content: 'I need to design a chat application like WhatsApp that can handle millions of users. What should I focus on first?',
        role: 'user' as const,
        timestamp: new Date('2024-01-12T14:30:00Z'),
        type: 'text' as const
      },
      {
        id: 'chat-msg-2',
        content: `Excellent question! Chat systems are fascinating because they require **real-time communication** at massive scale. Let's break down the core requirements:

**Core Features:**
• **One-on-one messaging** with instant delivery
• **Group chats** with hundreds of participants
• **Media sharing** (images, videos, documents)
• **Message persistence** and history
• **End-to-end encryption** for privacy
• **Read receipts** and delivery confirmations
• **Online/offline status** indicators

**Scale Considerations:**
• 1 billion users, 10% active simultaneously
• 100 billion messages per day
• Average message size: 100 bytes
• Peak traffic: 5x average during events

**Key Technical Challenges:**
1. How do we deliver messages in real-time?
2. How do we handle offline users?
3. How do we manage group chat fan-out?

Which aspect interests you most?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-12T14:31:00Z'),
        type: 'text' as const
      },
      {
        id: 'chat-msg-3',
        content: 'Let\'s focus on real-time delivery first. I know WebSockets are important, but how do we handle millions of concurrent connections?',
        role: 'user' as const,
        timestamp: new Date('2024-01-12T14:33:00Z'),
        type: 'text' as const
      },
      {
        id: 'chat-msg-4',
        content: `Perfect choice! **Real-time delivery** is the heart of any chat system. Here's how to handle millions of concurrent connections:

**WebSocket Architecture:**

**1. Connection Management:**
• **Multiple WebSocket servers** (horizontal scaling)
• **Connection registry** in Redis to track user → server mapping
• **Load balancer** with sticky sessions or consistent hashing
• **Connection pooling** to optimize resource usage

**2. Message Flow:**
\`\`\`
User A → WebSocket Server 1 → Message Queue → WebSocket Server 2 → User B
\`\`\`

**3. Scalability Patterns:**
• **Stateless WebSocket servers** for easy horizontal scaling
• **Message queue** (Kafka/RabbitMQ) for reliable delivery
• **Connection heartbeat** to detect disconnects
• **Graceful failover** when servers go down

**4. Optimization Techniques:**
• **Connection multiplexing** for multiple conversations
• **Binary protocols** (Protocol Buffers) instead of JSON
• **Message batching** for high-frequency users

Would you like to dive into the database design for message storage?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-12T14:35:00Z'),
        type: 'text' as const
      },
      // Early assessment
      {
        id: 'chat-msg-5',
        content: '🎯 **Assessment Complete**\n\n**Overall Score:** 3.3/5.0 (Confidence: 4.0/5.0)\n\n**Summary:** Good understanding of real-time messaging challenges and WebSocket scaling patterns. Strong focus on connection management.\n\n**Detailed Feedback:** You\'ve correctly identified WebSockets as the core technology and understand the need for horizontal scaling. Your questions show good intuition about the complexity of handling millions of connections.\n\n**Recommendations:**\n• Explore message persistence and database design\n• Consider offline user handling strategies\n• Think about security and encryption requirements\n\n**Next Steps:**\n• Design the message storage schema\n• Plan for offline message delivery\n• Consider group chat scalability challenges',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-12T14:37:00Z'),
        type: 'text' as const,
        metadata: {
          topic: 'Chat System Design',
          difficulty: 'advanced' as const,
          assessment: {
            requirements_analysis: 4,
            system_architecture: 3,
            technical_deep_dive: 4,
            scale_performance: 3,
            reliability_fault_tolerance: 2,
            communication_thought_process: 4
          }
        }
      },
      {
        id: 'chat-msg-6',
        content: 'Yes, let\'s design the database schema. I think we need tables for users, conversations, messages, and maybe message_participants for group chats?',
        role: 'user' as const,
        timestamp: new Date('2024-01-12T14:38:00Z'),
        type: 'text' as const
      },
      {
        id: 'chat-msg-7',
        content: `Excellent thinking! You've identified the core entities. Let me expand on your schema with WhatsApp-scale considerations:

**Core Tables:**

**Users Table:**
\`\`\`sql
id, phone_number, username, last_seen, status, public_key
\`\`\`

**Conversations Table:**
\`\`\`sql
id, type (direct/group), name, created_by, created_at, last_message_at
\`\`\`

**Messages Table:**
\`\`\`sql
id, conversation_id, sender_id, content, message_type, timestamp, edited_at
\`\`\`

**Conversation_Participants Table:**
\`\`\`sql
conversation_id, user_id, joined_at, role (admin/member), last_read_message_id
\`\`\`

**Key Design Decisions:**
• **Partition messages by conversation_id** for better performance
• **Use message_id for ordering** instead of timestamps
• **Denormalize last_message_at** in conversations for quick sorting
• **Store encryption keys** separately for security

**Advanced Considerations:**
• **Message retention policies** (delete after X days)
• **Media message handling** (store references, not content)
• **Message delivery status** tracking (sent, delivered, read)

Ready to design the overall system architecture?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-12T14:40:00Z'),
        type: 'text' as const
      },
      {
        id: 'chat-msg-8',
        content: 'I\'ve sketched the complete architecture showing API gateway, WebSocket servers, message queue, databases, and media storage.',
        role: 'user' as const,
        timestamp: new Date('2024-01-12T14:45:00Z'),
        type: 'text' as const
      },
      // Whiteboard and AI Design Review
      {
        id: 'chat-msg-9',
        content: 'Here\'s your whiteboard design:\n\n![Chat System Architecture](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgdmlld0JveD0iMCAwIDgwMCA2MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNjAwIiBmaWxsPSIjMWYyOTM3Ii8+CjwhLS0gQVBJIEdhdGV3YXkgLS0+CjxyZWN0IHg9IjM1MCIgeT0iNTAiIHdpZHRoPSIxMDAiIGhlaWdodD0iNTAiIGZpbGw9IiNmNTk2NDAiIHN0cm9rZT0iI2VhNTgwYyIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjQwMCIgeT0iODAiIGZpbGw9IndoaXRlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTEiIGZvbnQtd2VpZ2h0PSJib2xkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5BUEkgR2F0ZXdheTwvdGV4dD4KCjwhLS0gV2ViU29ja2V0IFNlcnZlcnMgLS0+CjxyZWN0IHg9IjEwMCIgeT0iMTgwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjUwIiBmaWxsPSIjMTBiOTgxIiBzdHJva2U9IiMwNTk2NjkiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSIxNTAiIHk9IjIxMCIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMCIgZm9udC13ZWlnaHQ9ImJvbGQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPldlYlNvY2tldCAxPC90ZXh0PgoKPHJlY3QgeD0iMzUwIiB5PSIxODAiIHdpZHRoPSIxMDAiIGhlaWdodD0iNTAiIGZpbGw9IiMxMGI5ODEiIHN0cm9rZT0iIzA1OTY2OSIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjQwMCIgeT0iMjEwIiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+V2ViU29ja2V0IDI8L3RleHQ+Cgo8cmVjdCB4PSI2MDAiIHk9IjE4MCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI1MCIgZmlsbD0iIzEwYjk4MSIgc3Ryb2tlPSIjMDU5NjY5IiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSI2NTAiIHk9IjIxMCIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMCIgZm9udC13ZWlnaHQ9ImJvbGQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPldlYlNvY2tldCAzPC90ZXh0PgoKPCEtLSBLYWZrYSBRdWV1ZSAtLT4KPHJlY3QgeD0iMzUwIiB5PSIzMDAiIHdpZHRoPSIxMDAiIGhlaWdodD0iNTAiIGZpbGw9IiNkYzI2MjYiIHN0cm9rZT0iI2I5MTc2MyIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjQwMCIgeT0iMzMwIiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjExIiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+S2Fma2EgUXVldWU8L3RleHQ+Cgo8IS0tIERhdGFiYXNlcyAtLT4KPHJlY3QgeD0iMTAwIiB5PSI0NTAiIHdpZHRoPSIxMDAiIGhlaWdodD0iNTAiIGZpbGw9IiNhODU1ZjciIHN0cm9rZT0iIzkzMzNlYSIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjE1MCIgeT0iNDgwIiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+TWVzc2FnZSBEQjwvdGV4dD4KCjxyZWN0IHg9IjYwMCIgeT0iNDUwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjUwIiBmaWxsPSIjYTg1NWY3IiBzdHJva2U9IiM5MzMzZWEiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSI2NTAiIHk9IjQ4MCIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMCIgZm9udC13ZWlnaHQ9ImJvbGQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPk1lZGlhIFN0b3JlPC90ZXh0PgoKPCEtLSBDb25uZWN0aW9ucyAtLT4KPGxpbmUgeDE9IjQwMCIgeTE9IjEwMCIgeDI9IjE1MCIgeTI9IjE4MCIgc3Ryb2tlPSIjOWNhM2FmIiBzdHJva2Utd2lkdGg9IjIiLz4KPGxpbmUgeDE9IjQwMCIgeTE9IjEwMCIgeDI9IjQwMCIgeTI9IjE4MCIgc3Ryb2tlPSIjOWNhM2FmIiBzdHJva2Utd2lkdGg9IjIiLz4KPGxpbmUgeDE9IjQwMCIgeTE9IjEwMCIgeDI9IjY1MCIgeTI9IjE4MCIgc3Ryb2tlPSIjOWNhM2FmIiBzdHJva2Utd2lkdGg9IjIiLz4KCjxsaW5lIHgxPSIxNTAiIHkxPSIyMzAiIHgyPSI0MDAiIHkyPSIzMDAiIHN0cm9rZT0iIzljYTNhZiIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxsaW5lIHgxPSI0MDAiIHkxPSIyMzAiIHgyPSI0MDAiIHkyPSIzMDAiIHN0cm9rZT0iIzljYTNhZiIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxsaW5lIHgxPSI2NTAiIHkxPSIyMzAiIHgyPSI0MDAiIHkyPSIzMDAiIHN0cm9rZT0iIzljYTNhZiIgc3Ryb2tlLXdpZHRoPSIyIi8+Cgo8bGluZSB4MT0iNDAwIiB5MT0iMzUwIiB4Mj0iMTUwIiB5Mj0iNDUwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMiIvPgo8bGluZSB4MT0iNDAwIiB5MT0iMzUwIiB4Mj0iNjUwIiB5Mj0iNDUwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMiIvPgo8L3N2Zz4=)',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-12T14:46:00Z'),
        type: 'text' as const
      },
      {
        id: 'chat-msg-10',
        content: `🎨 **AI Design Review of Your Chat System Architecture:**

**Strengths:**
✅ **Excellent scalability approach** with multiple WebSocket servers
✅ **Smart use of Kafka** for reliable message queuing
✅ **Proper separation** of message DB and media storage
✅ **API Gateway pattern** for load distribution

**Areas for Enhancement:**
🔍 **Missing Components:**
• **Redis cluster** for connection registry and session management
• **Push notification service** for offline users
• **Rate limiting service** to prevent spam
• **Presence service** for online/offline status

🔍 **Architecture Improvements:**
• **Database sharding strategy** not clearly defined
• **Encryption service** for E2E encryption key management
• **Analytics service** for message delivery metrics
• **CDN** for media file distribution

**Scalability Considerations:**
• How do you handle WebSocket server failures?
• What's your strategy for cross-region deployment?
• How do you manage message ordering in group chats?

**Overall Score: 8/10** - Strong foundation with room for production-ready enhancements.`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-12T14:47:00Z'),
        type: 'text' as const
      },
      // Final assessment
      {
        id: 'chat-msg-11',
        content: '🎯 **Assessment Complete**\n\n**Overall Score:** 4.3/5.0 (Confidence: 4.6/5.0)\n\n**Summary:** Excellent comprehensive chat system design with strong understanding of real-time messaging architecture and scalability patterns.\n\n**Detailed Feedback:** Your final architecture demonstrates production-level thinking with proper WebSocket scaling, message queuing, and database design. You\'ve shown strong progression from initial concepts to advanced implementation details.\n\n**Recommendations:**\n• Add more details about encryption and security measures\n• Consider disaster recovery and backup strategies\n• Think about cross-region deployment challenges\n\n**Next Steps:**\n• Study WhatsApp and Signal engineering blogs\n• Practice implementing WebSocket connection management\n• Explore advanced topics like message encryption protocols',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-12T14:50:00Z'),
        type: 'text' as const,
        metadata: {
          topic: 'Chat System Design',
          difficulty: 'advanced' as const,
          assessment: {
            requirements_analysis: 5,
            system_architecture: 4,
            technical_deep_dive: 5,
            scale_performance: 4,
            reliability_fault_tolerance: 4,
            communication_thought_process: 5
          }
        }
      }
    ]
  },
  'session_3': {
    id: 'session_3',
    title: 'E-commerce Platform',
    messages: [
      {
        id: 'ecom-msg-1',
        content: 'I want to design an e-commerce platform like Amazon that can handle Black Friday traffic. Where should I start?',
        role: 'user' as const,
        timestamp: new Date('2024-01-11T09:15:00Z'),
        type: 'text' as const
      },
      {
        id: 'ecom-msg-2',
        content: `Excellent choice! E-commerce platforms like Amazon are among the most complex distributed systems. Black Friday specifically brings unique challenges. Let's start with the foundation:

**Core E-commerce Components:**
• **Product Catalog** with millions of items
• **Inventory Management** with real-time updates
• **Shopping Cart** and session management
• **Order Processing** pipeline
• **Payment Processing** with multiple gateways
• **Search and Recommendation** engines
• **User Management** and reviews

**Black Friday Scale Challenges:**
• **100x normal traffic** spikes
• **Flash sales** with limited inventory
• **Global load** across multiple regions
• **Payment processing** bottlenecks
• **Fraud detection** at scale

**Architecture Priorities:**
1. **Horizontal scalability** for traffic spikes
2. **Inventory consistency** to prevent overselling
3. **Fast search and discovery** for product catalog
4. **Reliable payment processing** pipeline

Which component would you like to tackle first?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-11T09:16:30Z'),
        type: 'text' as const
      },
      {
        id: 'ecom-msg-3',
        content: 'Let\'s start with the product catalog and search functionality. That seems like the foundation, plus the catalog needs to support millions of products.',
        role: 'user' as const,
        timestamp: new Date('2024-01-11T09:18:00Z'),
        type: 'text' as const
      },
      {
        id: 'ecom-msg-4',
        content: `Excellent choice! **Product catalog and search** are the foundation of any e-commerce platform. Here's a comprehensive approach:

**Product Catalog Architecture:**

**1. Database Design:**
\`\`\`sql
Products: id, title, description, brand_id, category_id, price, created_at
Product_Variants: id, product_id, size, color, sku, inventory_count
Categories: id, name, parent_id, level (hierarchical)
Product_Images: id, product_id, image_url, display_order
\`\`\`

**2. Search Infrastructure:**
• **Elasticsearch cluster** for full-text search
• **Search index structure:**
  - Product data (title, description, brand)
  - Faceted search (category, price range, ratings)
  - Auto-complete suggestions
  - Personalized ranking factors

**3. Performance Optimizations:**
• **CDN** for product images and static content
• **Redis caching** for popular product data
• **Database read replicas** for search queries
• **Pagination** with cursor-based navigation

**4. Search Features:**
• **Fuzzy matching** for typos
• **Faceted filtering** (price, brand, ratings, etc.)
• **Auto-complete** and **typo tolerance**
• **Personalized ranking** based on user history

Should we design the inventory management system next?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-11T09:20:00Z'),
        type: 'text' as const
      },
      // Early assessment
      {
        id: 'ecom-msg-5',
        content: '🎯 **Assessment Complete**\n\n**Overall Score:** 3.5/5.0 (Confidence: 4.1/5.0)\n\n**Summary:** Strong understanding of e-commerce catalog requirements and search infrastructure. Good focus on scalability and performance.\n\n**Detailed Feedback:** You\'ve correctly identified the product catalog as the foundation and shown good understanding of search requirements. Your approach to Elasticsearch and caching shows solid architectural thinking.\n\n**Recommendations:**\n• Explore inventory management and consistency challenges\n• Consider microservices architecture for different components\n• Think about payment processing and security requirements\n\n**Next Steps:**\n• Design inventory management for flash sales\n• Plan the order processing pipeline\n• Consider fraud detection and security measures',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-11T09:22:00Z'),
        type: 'text' as const,
        metadata: {
          topic: 'E-commerce Platform Design',
          difficulty: 'advanced' as const,
          assessment: {
            requirements_analysis: 4,
            system_architecture: 3,
            technical_deep_dive: 4,
            scale_performance: 3,
            reliability_fault_tolerance: 3,
            communication_thought_process: 4
          }
        }
      },
      {
        id: 'ecom-msg-6',
        content: 'Yes, let\'s tackle inventory management. This seems critical for preventing overselling during flash sales.',
        role: 'user' as const,
        timestamp: new Date('2024-01-11T09:23:00Z'),
        type: 'text' as const
      },
      {
        id: 'ecom-msg-7',
        content: `**Inventory Management** is absolutely critical! Overselling during flash sales can be disastrous. Here's a robust approach:

**Inventory Architecture:**

**1. Multi-Level Inventory System:**
\`\`\`sql
Inventory: product_variant_id, warehouse_id, available_qty, reserved_qty
Reservations: id, product_variant_id, user_id, qty, expires_at, status
Inventory_Logs: id, product_variant_id, change_type, qty_change, timestamp
\`\`\`

**2. Flash Sale Strategy:**
• **Pre-reserve inventory** for flash sales in separate pool
• **Distributed locks** using Redis for atomic updates
• **Event-driven architecture** for inventory changes
• **Real-time inventory** sync across all services

**3. Consistency Mechanisms:**
• **Optimistic locking** for normal operations
• **Pessimistic locking** for high-contention items
• **Saga pattern** for cross-service transactions
• **Eventual consistency** with compensation

**4. Performance Optimizations:**
• **Cache hot inventory** in Redis
• **Batch inventory updates** for efficiency
• **Separate read/write** database instances
• **Queue-based** inventory adjustments

Ready to design the complete microservices architecture?`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-11T09:25:30Z'),
        type: 'text' as const
      },
      {
        id: 'ecom-msg-8',
        content: 'I\'ve sketched the complete architecture showing microservices, databases, caching layers, and external integrations for payments and logistics.',
        role: 'user' as const,
        timestamp: new Date('2024-01-11T09:30:00Z'),
        type: 'text' as const
      },
      // Whiteboard and AI Design Review
      {
        id: 'ecom-msg-9',
        content: 'Here\'s your comprehensive e-commerce architecture:\n\n![E-commerce Platform Architecture](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgdmlld0JveD0iMCAwIDgwMCA2MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNjAwIiBmaWxsPSIjMWYyOTM3Ii8+CjwhLS0gQVBJIEdhdGV3YXkgLS0+CjxyZWN0IHg9IjM1MCIgeT0iMzAiIHdpZHRoPSIxMDAiIGhlaWdodD0iNDAiIGZpbGw9IiNmNTk2NDAiIHN0cm9rZT0iI2VhNTgwYyIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjQwMCIgeT0iNTUiIGZpbGw9IndoaXRlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTAiIGZvbnQtd2VpZ2h0PSJib2xkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5BUEkgR2F0ZXdheTwvdGV4dD4KCjwhLS0gTWljcm9zZXJ2aWNlcyAtLT4KPHJlY3QgeD0iNTAiIHk9IjEyMCIgd2lkdGg9IjkwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjMzU4NGU0IiBzdHJva2U9IiMyNTYzZWIiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSI5NSIgeT0iMTQ1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjkiIGZvbnQtd2VpZ2h0PSJib2xkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5Qcm9kdWN0IFNlcnZpY2U8L3RleHQ+Cgo8cmVjdCB4PSIxNzAiIHk9IjEyMCIgd2lkdGg9IjkwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjMzU4NGU0IiBzdHJva2U9IiMyNTYzZWIiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSIyMTUiIHk9IjE0NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Q2FydCBTZXJ2aWNlPC90ZXh0PgoKPHJlY3QgeD0iMjkwIiB5PSIxMjAiIHdpZHRoPSI5MCIgaGVpZ2h0PSI0MCIgZmlsbD0iIzM1ODRlNCIgc3Ryb2tlPSIjMjU2M2ViIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSIzMzUiIHk9IjE0NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+T3JkZXIgU2VydmljZTwvdGV4dD4KCjxyZWN0IHg9IjQxMCIgeT0iMTIwIiB3aWR0aD0iOTAiIGhlaWdodD0iNDAiIGZpbGw9IiMzNTg0ZTQiIHN0cm9rZT0iIzI1NjNlYiIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjQ1NSIgeT0iMTQ1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjkiIGZvbnQtd2VpZ2h0PSJib2xkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5QYXltZW50IFNlcnZpY2U8L3RleHQ+Cgo8cmVjdCB4PSI1MzAiIHk9IjEyMCIgd2lkdGg9IjkwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjMzU4NGU0IiBzdHJva2U9IiMyNTYzZWIiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSI1NzUiIHk9IjE0NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+SW52ZW50b3J5IFNlcnZpY2U8L3RleHQ+Cgo8cmVjdCB4PSI2NTAiIHk9IjEyMCIgd2lkdGg9IjkwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjMzU4NGU0IiBzdHJva2U9IiMyNTYzZWIiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSI2OTUiIHk9IjE0NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+U2VhcmNoIFNlcnZpY2U8L3RleHQ+Cgo8IS0tIERhdGFiYXNlcyAtLT4KPHJlY3QgeD0iMTAwIiB5PSIyNDAiIHdpZHRoPSI4MCIgaGVpZ2h0PSI0MCIgZmlsbD0iI2E4NTVmNyIgc3Ryb2tlPSIjOTMzM2VhIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSIxNDAiIHk9IjI2NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+UHJvZHVjdCBEQjwvdGV4dD4KCjxyZWN0IHg9IjIxMCIgeT0iMjQwIiB3aWR0aD0iODAiIGhlaWdodD0iNDAiIGZpbGw9IiNhODU1ZjciIHN0cm9rZT0iIzkzMzNlYSIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjI1MCIgeT0iMjY1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjkiIGZvbnQtd2VpZ2h0PSJib2xkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5PcmRlciBEQjwvdGV4dD4KCjxyZWN0IHg9IjMyMCIgeT0iMjQwIiB3aWR0aD0iODAiIGhlaWdodD0iNDAiIGZpbGw9IiNhODU1ZjciIHN0cm9rZT0iIzkzMzNlYSIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjM2MCIgeT0iMjY1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjkiIGZvbnQtd2VpZ2h0PSJib2xkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5Vc2VyIERCPC90ZXh0PgoKPCEtLSBFbGFzdGljc2VhcmNoIC0tPgo8cmVjdCB4PSI2MDAiIHk9IjI0MCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI0MCIgZmlsbD0iI2Y1OTY0MCIgc3Ryb2tlPSIjZWE1ODBjIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSI2NTAiIHk9IjI2NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+RWxhc3RpY3NlYXJjaDwvdGV4dD4KCjwhLS0gUmVkaXMgQ2FjaGUgLS0+CjxyZWN0IHg9IjM1MCIgeT0iMzYwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjZWY0NDQ0IiBzdHJva2U9IiNkYzI2MjYiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSI0MDAiIHk9IjM4NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+UmVkaXMgQ2FjaGU8L3RleHQ+Cgo8IS0tIEthZmthIC0tPgo8cmVjdCB4PSI1MDAiIHk9IjM2MCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI0MCIgZmlsbD0iI2RjMjYyNiIgc3Ryb2tlPSIjYjkxNzYzIiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSI1NTAiIHk9IjM4NSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+S2Fma2EgUXVldWU8L3RleHQ+Cgo8IS0tIEV4dGVybmFsIFNlcnZpY2VzIC0tPgo8cmVjdCB4PSI1MCIgeT0iNDgwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjMTBiOTgxIiBzdHJva2U9IiMwNTk2NjkiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSIxMDAiIHk9IjUwNSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+UGF5bWVudCBHYXRld2F5PC90ZXh0PgoKPHJlY3QgeD0iMjAwIiB5PSI0ODAiIHdpZHRoPSIxMDAiIGhlaWdodD0iNDAiIGZpbGw9IiMxMGI5ODEiIHN0cm9rZT0iIzA1OTY2OSIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjI1MCIgeT0iNTA1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjkiIGZvbnQtd2VpZ2h0PSJib2xkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5TaGlwcGluZyBBUEk8L3RleHQ+Cgo8cmVjdCB4PSI2MDAiIHk9IjQ4MCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSI0MCIgZmlsbD0iIzEwYjk4MSIgc3Ryb2tlPSIjMDU5NjY5IiBzdHJva2Utd2lkdGg9IjIiLz4KPHR4dCB4PSI2NTAiIHk9IjUwNSIgZmlsbD0id2hpdGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSI5IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Tm90aWZpY2F0aW9uIEFQSTwvdGV4dD4KCjwhLS0gQ29ubmVjdGlvbnMgLS0+CjxsaW5lIHgxPSI0MDAiIHkxPSI3MCIgeDI9IjIxNSIgeTI9IjEyMCIgc3Ryb2tlPSIjOWNhM2FmIiBzdHJva2Utd2lkdGg9IjEuNSIvPgo8bGluZSB4MT0iNDAwIiB5MT0iNzAiIHgyPSI0NTUiIHkyPSIxMjAiIHN0cm9rZT0iIzljYTNhZiIgc3Ryb2tlLXdpZHRoPSIxLjUiLz4KPGxpbmUgeDE9IjQwMCIgeTE9IjcwIiB4Mj0iNjk1IiB5Mj0iMTIwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMS41Ii8+Cgo8bGluZSB4MT0iOTUiIHkxPSIxNjAiIHgyPSIxNDAiIHkyPSIyNDAiIHN0cm9rZT0iIzljYTNhZiIgc3Ryb2tlLXdpZHRoPSIxLjUiLz4KPGxpbmUgeDE9IjMzNSIgeTE9IjE2MCIgeDI9IjI1MCIgeTI9IjI0MCIgc3Ryb2tlPSIjOWNhM2FmIiBzdHJva2Utd2lkdGg9IjEuNSIvPgo8bGluZSB4MT0iNjk1IiB5MT0iMTYwIiB4Mj0iNjUwIiB5Mj0iMjQwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMS41Ii8+Cgo8bGluZSB4MT0iNDU1IiB5MT0iMTYwIiB4Mj0iMTAwIiB5Mj0iNDgwIiBzdHJva2U9IiM5Y2EzYWYiIHN0cm9rZS13aWR0aD0iMS41Ii8+Cjwvc3ZnPgo=)',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-11T09:31:00Z'),
        type: 'text' as const
      },
      {
        id: 'ecom-msg-10',
        content: `🎨 **AI Design Review of Your E-commerce Platform Architecture:**

**Strengths:**
✅ **Excellent microservices decomposition** with clear service boundaries
✅ **Comprehensive data layer** with specialized databases
✅ **Smart caching strategy** with Redis and Elasticsearch
✅ **Proper external integrations** for payments and logistics

**Areas for Enhancement:**
🔍 **Missing Components:**
• **CDN layer** for static content and product images
• **API rate limiting** and throttling mechanisms
• **Fraud detection service** for payment security
• **Recommendation engine** for personalized product suggestions
• **Monitoring and observability** stack (Prometheus, Grafana)

🔍 **Architecture Improvements:**
• **Database replication strategy** for high availability
• **Cross-region deployment** for global performance
• **Circuit breaker pattern** for service resilience
• **Event sourcing** for audit trails and order history

**Scalability Considerations:**
• How do you handle flash sale traffic spikes?
• What's your strategy for inventory synchronization across regions?
• How do you ensure payment consistency during high concurrency?

**Overall Score: 8.5/10** - Enterprise-ready foundation with excellent scalability planning.`,
        role: 'assistant' as const,
        timestamp: new Date('2024-01-11T09:32:00Z'),
        type: 'text' as const
      },
      // Final assessment
      {
        id: 'ecom-msg-11',
        content: '🎯 **Assessment Complete**\n\n**Overall Score:** 4.5/5.0 (Confidence: 4.7/5.0)\n\n**Summary:** Outstanding comprehensive e-commerce platform design with enterprise-level thinking and excellent scalability planning.\n\n**Detailed Feedback:** Your architecture demonstrates deep understanding of complex e-commerce challenges including inventory consistency, payment processing, and Black Friday scale requirements. The microservices decomposition and technology choices show production-ready thinking.\n\n**Recommendations:**\n• Add more details about fraud detection and security measures\n• Consider machine learning for personalization and recommendations\n• Think about international expansion and multi-currency support\n\n**Next Steps:**\n• Study Amazon and eBay engineering blogs\n• Practice implementing payment processing workflows\n• Explore advanced topics like dynamic pricing and inventory optimization',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-11T09:35:00Z'),
        type: 'text' as const,
        metadata: {
          topic: 'E-commerce Platform Design',
          difficulty: 'advanced' as const,
          assessment: {
            requirements_analysis: 5,
            system_architecture: 5,
            technical_deep_dive: 5,
            scale_performance: 4,
            reliability_fault_tolerance: 4,
            communication_thought_process: 5
          }
        }
      }
    ]
  }
}

export type DemoSessionId = keyof typeof demoSessions