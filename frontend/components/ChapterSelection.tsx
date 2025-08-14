'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { 
  MessageSquare, 
  Share2, 
  Database, 
  Zap, 
  ShoppingCart, 
  Video,
  Clock,
  Users
} from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'

interface Chapter {
  id: string
  title: string
  description: string
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
  duration: string
  icon: React.ComponentType<{ className?: string }>
  topics: string[]
}

const chapters: Chapter[] = [
  {
    id: 'twitter',
    title: 'Design Twitter/X',
    description: 'Learn to design a social media platform with millions of users, focusing on scalability, real-time features, and data consistency.',
    difficulty: 'Intermediate',
    duration: '45-60 min',
    icon: MessageSquare,
    topics: ['Load Balancing', 'Caching', 'Database Sharding', 'Real-time Updates', 'CDN']
  },
  {
    id: 'url-shortener',
    title: 'URL Shortener (bit.ly)',
    description: 'Design a URL shortening service focusing on high availability, analytics, and custom domains.',
    difficulty: 'Beginner',
    duration: '30-45 min',
    icon: Share2,
    topics: ['URL Encoding', 'Database Design', 'Caching', 'Analytics', 'Rate Limiting']
  },
  {
    id: 'chat-system',
    title: 'Chat System (WhatsApp)',
    description: 'Build a real-time messaging system with group chats, media sharing, and message delivery guarantees.',
    difficulty: 'Advanced',
    duration: '60-75 min',
    icon: MessageSquare,
    topics: ['WebSockets', 'Message Queues', 'End-to-End Encryption', 'Push Notifications']
  },
  {
    id: 'newsfeed',
    title: 'News Feed System',
    description: 'Create a personalized news feed system like Facebook or LinkedIn with timeline generation and ranking.',
    difficulty: 'Advanced',
    duration: '60-90 min',
    icon: Database,
    topics: ['Timeline Generation', 'Recommendation Algorithms', 'Cache Strategies', 'Fan-out']
  },
  {
    id: 'ride-sharing',
    title: 'Ride Sharing (Uber)',
    description: 'Design a ride-sharing platform with real-time location tracking, matching algorithms, and payment processing.',
    difficulty: 'Advanced',
    duration: '75-90 min',
    icon: Zap,
    topics: ['Geospatial Indexing', 'Real-time Tracking', 'Matching Algorithms', 'Payment Systems']
  },
  {
    id: 'ecommerce',
    title: 'E-commerce Platform',
    description: 'Build an online shopping platform with inventory management, order processing, and recommendation systems.',
    difficulty: 'Intermediate',
    duration: '60-75 min',
    icon: ShoppingCart,
    topics: ['Inventory Management', 'Order Processing', 'Payment Gateway', 'Search & Recommendations']
  },
  {
    id: 'video-streaming',
    title: 'Video Streaming (YouTube)',
    description: 'Design a video streaming platform with video processing, CDN distribution, and recommendation algorithms.',
    difficulty: 'Advanced',
    duration: '75-90 min',
    icon: Video,
    topics: ['Video Processing', 'CDN', 'Adaptive Streaming', 'Content Recommendation']
  },
  {
    id: 'rate-limiter',
    title: 'Rate Limiter',
    description: 'Implement a distributed rate limiting system with different algorithms and use cases.',
    difficulty: 'Intermediate',
    duration: '30-45 min',
    icon: Clock,
    topics: ['Token Bucket', 'Sliding Window', 'Distributed Systems', 'Redis']
  }
]

interface ChapterSelectionProps {
  onChapterSelect: (chapterId: string) => void
  selectedChapter?: string
}

export function ChapterSelection({ onChapterSelect, selectedChapter }: ChapterSelectionProps) {
  const { theme } = useTheme()

  const getDifficultyColor = (difficulty: Chapter['difficulty']) => {
    switch (difficulty) {
      case 'Beginner':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'Intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'Advanced':
        return 'bg-red-100 text-red-800 border-red-200'
    }
  }

  const getDifficultyColorDark = (difficulty: Chapter['difficulty']) => {
    switch (difficulty) {
      case 'Beginner':
        return 'bg-green-900/30 text-green-300 border-green-700'
      case 'Intermediate':
        return 'bg-yellow-900/30 text-yellow-300 border-yellow-700'
      case 'Advanced':
        return 'bg-red-900/30 text-red-300 border-red-700'
    }
  }

  return (
    <div className={`min-h-screen p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className={`text-3xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Choose Your Learning Path
          </h1>
          <p className={`text-lg ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
            Select a system design challenge to begin your interactive learning session
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {chapters.map((chapter) => {
            const IconComponent = chapter.icon
            const isSelected = selectedChapter === chapter.id
            
            return (
              <Card 
                key={chapter.id}
                className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
                  theme === 'dark' 
                    ? 'bg-gray-800 border-gray-700 hover:bg-gray-750' 
                    : 'bg-white border-gray-200 hover:bg-gray-50'
                } ${
                  isSelected 
                    ? (theme === 'dark' 
                        ? 'ring-2 ring-blue-500 bg-blue-900/20' 
                        : 'ring-2 ring-blue-500 bg-blue-50'
                      ) 
                    : ''
                }`}
                onClick={() => onChapterSelect(chapter.id)}
                data-testid={`chapter-${chapter.id}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        theme === 'dark' ? 'bg-blue-600/20' : 'bg-blue-100'
                      }`}>
                        <IconComponent className={`h-6 w-6 ${
                          theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                        }`} />
                      </div>
                      <div>
                        <CardTitle className={`text-lg ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                          {chapter.title}
                        </CardTitle>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`px-2 py-1 text-xs rounded border ${
                            theme === 'dark' 
                              ? getDifficultyColorDark(chapter.difficulty)
                              : getDifficultyColor(chapter.difficulty)
                          }`}>
                            {chapter.difficulty}
                          </span>
                          <span className={`text-xs flex items-center ${
                            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            <Clock className="h-3 w-3 mr-1" />
                            {chapter.duration}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="pt-0">
                  <p className={`text-sm mb-4 leading-relaxed ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                    {chapter.description}
                  </p>

                  <div className="mb-4">
                    <h4 className={`text-xs font-medium mb-2 ${
                      theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Key Topics:
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {chapter.topics.map((topic, index) => (
                        <span 
                          key={index}
                          className={`px-2 py-1 text-xs rounded ${
                            theme === 'dark' 
                              ? 'bg-gray-700 text-gray-300' 
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>

                  <Button 
                    className="w-full"
                    variant={isSelected ? "default" : "outline"}
                  >
                    {isSelected ? 'Selected' : 'Start Learning'}
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {selectedChapter && (
          <div className="mt-8 text-center">
            <Button 
              size="lg"
              className="px-8 py-3"
              onClick={() => {
                // This would normally navigate to the chat interface with the selected chapter
                window.location.href = '/chat'
              }}
              data-testid="continue-with-chapter"
            >
              Continue with Selected Chapter
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}