'use client'

import React, { useState, useEffect } from 'react'
import { ChatInterface, Message } from '@/components/ChatInterface'
import { AuthUI } from '@/components/AuthUI'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { BookOpen, Target, TrendingUp, Clock } from 'lucide-react'

// Mock user data - in real app this would come from authentication service
const mockUser = {
    name: 'John Doe',
    email: 'john@example.com',
    skillLevel: 'intermediate' as const
}

// Mock session data
const mockSessionInfo = {
    topic: 'Social Media Platform Design',
    difficulty: 'intermediate',
    progress: 35
}

export default function ChatPage() {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [messages, setMessages] = useState<Message[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isTyping, setIsTyping] = useState(false)

    // Mock authentication check
    useEffect(() => {
        // Simulate checking authentication status
        const checkAuth = setTimeout(() => {
            setIsAuthenticated(true)
        }, 1000)

        return () => clearTimeout(checkAuth)
    }, [])

    const handleSendMessage = async (message: string) => {
        if (!message.trim()) return

        const userMessage: Message = {
            id: Date.now().toString(),
            content: message,
            role: 'user',
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setIsTyping(true)
        setError(null)

        try {
            // Simulate API call delay
            await new Promise(resolve => setTimeout(resolve, 1000))

            // Mock AI response
            const aiResponse: Message = {
                id: (Date.now() + 1).toString(),
                content: `Thank you for your question about "${message}". This is a mock response that would normally come from the AI system design learning assistant. In a real implementation, this would provide detailed guidance, examples, and potentially assessment scores.`,
                role: 'assistant',
                timestamp: new Date(),
                metadata: {
                    topic: 'System Design',
                    difficulty: 'intermediate',
                    assessment: {
                        requirements_analysis: Math.floor(Math.random() * 5) + 1,
                        system_architecture: Math.floor(Math.random() * 5) + 1,
                        technical_deep_dive: Math.floor(Math.random() * 5) + 1,
                        scale_performance: Math.floor(Math.random() * 5) + 1,
                        reliability_fault_tolerance: Math.floor(Math.random() * 5) + 1,
                        communication_thought_process: Math.floor(Math.random() * 5) + 1
                    }
                }
            }

            setMessages(prev => [...prev, aiResponse])
        } catch (err) {
            setError('Failed to get AI response. Please try again.')
        } finally {
            setIsTyping(false)
        }
    }

    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
                <AuthUI onAuthenticated={() => setIsAuthenticated(true)} />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center gap-3">
                            <BookOpen className="w-8 h-8 text-blue-600" />
                            <h1 className="text-xl font-bold text-gray-900">System Design AI</h1>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-600">Welcome,</span>
                                <span className="font-medium text-gray-900">{mockUser.name}</span>
                                <Badge variant="outline">{mockUser.skillLevel}</Badge>
                            </div>

                            <Button variant="outline" size="sm">
                                Sign Out
                            </Button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Session Info */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <Card>
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Target className="w-5 h-5 text-blue-600" />
                                <div>
                                    <CardTitle className="text-lg">Current Session</CardTitle>
                                    <p className="text-sm text-gray-600">Topic: {mockSessionInfo.topic}</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2">
                                    <Badge variant="secondary">{mockSessionInfo.difficulty}</Badge>
                                    <div className="flex items-center gap-2">
                                        <TrendingUp className="w-4 h-4 text-green-600" />
                                        <span className="text-sm text-gray-600">{mockSessionInfo.progress}% Complete</span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 text-sm text-gray-500">
                                    <Clock className="w-4 h-4" />
                                    <span>Session Time: 12:34</span>
                                </div>
                            </div>
                        </div>
                    </CardHeader>
                </Card>
            </div>

            {/* Main Chat Interface */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
                <ChatInterface
                    messages={messages}
                    onSendMessage={handleSendMessage}
                    isLoading={isLoading}
                    error={error}
                    isTyping={isTyping}
                />
            </div>
        </div>
    )
}
