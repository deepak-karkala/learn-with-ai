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
        imageData: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA+gAAAJYCAYAAADxHswlAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAABloSURBVHgB7d0xbttKEIDhJQW4BVuAWkAKcAFuASkg3YpwAe5ALcAFuAW7ALeAFOAW3AJSgFtwC04BacEtwAW4BaSAFJACTgEugW/+sWzJoiVbFDn/fIAB05Jl0ZY9OzPcmSdPnrwEAAC74N9/fr/88Z+fP/6d/jz7+fOXe/Tq5cs///h99//0y8+f733z1cs//jj7+fPb759ffnn/5dc//vPo5csXP//XcvPqyy+/WMdvv/3x8x+frn79w7vy28//9+9fLz78/Pnrh/fff//zn6/ffvtt49///p2/v/v6z7df/PGLf/v4+I+f//j+62+/fvfdo7/98vOP3377zdra9i+vv/zq/7765S//+cc//vOPL7/66qtvPnwwjt9//+Off/zx629//PGHX7/99tt/ffvtt/9//PjRr7/99s8//vj12y+//vbrz5///s0/f/7+3XfffPvl6w8fvnrx8sf3H7777us//vGPTz999913/++vv/76+bNPn36ff/7Fl6+//vrv//nPh89P/v3v//x6Nzr8+fPd7//8x9//9tdPHzx48Pn3//yyy8///d//+OOPb//97bcPf/z4z7ffvvv0y5dfvvvq5cufv//u258+ffrxk59++tEnn3zy3S/fvn+/TXn++eeffXZbhp7/+edfH9qXv//+u3ft6vvP//rrr//33Xc//Oc///nh+++//e6Db7/9+cNPP/38wy+//Pbrr/9z//33n3z22Wc/ffL555899tlnn3z88cef3r9//8H9+/c/eP/+/R/b7ds7/7V9e+fd+/ff//Ddd99/991PP33y008ffPzxJx999PFHH370yScfffLJJ5999tlnn3/++Wef/efrr77++quPP/74w/v333/w7rvv/+fdd9/958033/zvf/3rX//8v//7L7/88suPP//yy4+//PLj+w8fPvz7Dz/88Pf333//7kOHDj147733jh8+fHjy6NGj00ePHp08evTo5MGDBw8fPHhw8+DBg5NDhw7dOHjwYPbggQPfvfvu7Qf33nvfuu/tt+9ee/vt+9fevn3r2rVrbx07eux/rly58o8zZ878+6lTp1699tprJ65evfrw0qVLpWXLlqWCBQsWrlu3bt2OHTuOHjp06PZHH3308L333jty5MiR97dt2/bO1q1b39m2bds7+/bt++jQoUNvHzp06O+HDx8+fvjw4ZOHDh06ffTo0bOXL18+8+LFi9svX768efny5Y1Ll1JBhk4dPWps3Ljxld7e3l7r7e3t/d///d9+pnpNiL+QUgFEu3bt2v9dvXr1zt69e/ft27fv9Y8//vjtt996/cCBA5uPHDmy+siRI4sOHjx47Z133nn7nnvu+de77777zTvvvPPttWvX3rl69erNa9euXbt27dpr77777htvvPGGdRUXF2+4efPmhlu3bt26ffv2Xetk6tChQw8fPXr0+NGjR08fPnz41KFDh0799ttv17dt2/b2Bx98sOXf//732//9739//PbbbxrIj4MHXX/ooYceGDVr1qyZo8aOHj1qzKhRo0Z/4Q/+cKZfY8eOHTtm7Nixx98cPnz4wQ9HjBgxav/+/fuGjx8/fsSsWbNmzpo1a+asWbNmDho0aNCyNWvWzL169epVa9asWbNp06ZNixYtWrT+3LlzI6ZNmzZ91qxZs2bPnj179uzZs+fMmTNnzpw5c+bMmTNnzJgxY8aMGTNmzJgxY/r06dOnT58+ffr06dOnT58+ffqTEycuXLhw4cCBA/v3799/8ODBgwcPHjx48ODBgwcPnj558uTJEyZMmDBhwoQJEyZMmDBhwoQJEyZMmDBhwoQJEyZMmDBhwqRJkyZNmjRp0qRJkyZNmjRp0qRJkyZNmjRp0qRJkyZNmjRp0qRJkyZNmjRp0qRJkya1tbW1nT9//vyZM2fOnDlz5syZM2fOnDlz5syZM2fOnDlz5syZM2fOnDlz5syZMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMWPGjBkzZsyYMePBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
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
        content: `🎨 **Chat System Architecture Diagram:**

I've designed a comprehensive chat system architecture that handles real-time messaging at scale. Here are the key components I've included:

**Architecture Components:**
• **API Gateway** - Single entry point for all client requests
• **WebSocket Servers** - Multiple servers for real-time connections
• **Kafka Message Queue** - Reliable message delivery and persistence
• **Message Database** - Stores conversation history
• **Media Store** - Handles file uploads and media sharing

**Key Design Decisions:**
• Horizontal scaling with multiple WebSocket servers
• Kafka for guaranteed message delivery and ordering
• Separate media storage for performance optimization
• Connection registry in Redis for load balancing

This architecture can handle millions of concurrent connections while ensuring message reliability and low latency.`,
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
        content: `🎨 **E-commerce Platform Architecture Diagram:**

I've designed a comprehensive e-commerce platform architecture that can handle Black Friday scale traffic. Here are the key components I've included:

**Architecture Components:**
• **API Gateway** - Single entry point with load balancing
• **Microservices Layer** - Product, Cart, Order, Payment, Inventory, and Search services
• **Database Layer** - Specialized databases for different domains (Product DB, Order DB, User DB)
• **Elasticsearch** - Full-text search and product catalog indexing
• **Caching Layer** - Redis for session data and frequently accessed products
• **Message Queue** - Kafka for reliable order processing and inventory updates
• **External Services** - Payment Gateway, Shipping API, and Notification services

**Key Design Decisions:**
• Microservices architecture for independent scaling
• Separate databases for different domains to avoid bottlenecks
• Elasticsearch for fast product search and filtering
• Redis caching for hot products and user sessions
• Kafka for async processing of orders and inventory updates
• External API integrations for payments and logistics

This architecture can scale to handle 100x traffic spikes during Black Friday while maintaining data consistency and fast response times.`,
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