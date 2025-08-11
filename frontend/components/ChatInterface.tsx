'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar'
import { Badge } from './ui/badge'
import { ScrollArea } from './ui/scroll-area'
import { Separator } from './ui/separator'
import { Send, Bot, User, AlertCircle } from 'lucide-react'

export interface Message {
    id: string
    content: string
    role: 'user' | 'assistant'
    timestamp: Date
    isLoading?: boolean
    metadata?: {
        topic?: string
        difficulty?: 'beginner' | 'intermediate' | 'advanced'
        assessment?: {
            requirements_analysis?: number
            system_architecture?: number
            technical_deep_dive?: number
            scale_performance?: number
            reliability_fault_tolerance?: number
            communication_thought_process?: number
        }
    }
}

interface ChatInterfaceProps {
    messages: Message[]
    onSendMessage: (message: string) => Promise<void>
    isLoading?: boolean
    error?: string | null
    isTyping?: boolean
    className?: string
}

export function ChatInterface({
    messages,
    onSendMessage,
    isLoading = false,
    error = null,
    isTyping = false,
    className = ''
}: ChatInterfaceProps) {
    const [inputValue, setInputValue] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    useEffect(() => {
        if (!isLoading && !isTyping) {
            setIsSubmitting(false)
        }
    }, [isLoading, isTyping])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!inputValue.trim() || isSubmitting) return

        const message = inputValue.trim()
        setInputValue('')
        setIsSubmitting(true)

        try {
            await onSendMessage(message)
        } catch (error) {
            console.error('Failed to send message:', error)
        }
    }

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            if (inputValue.trim()) {
                const message = inputValue.trim()
                setInputValue('')
                setIsSubmitting(true)

                onSendMessage(message).catch((error) => {
                    console.error('Failed to send message:', error)
                    setIsSubmitting(false)
                })
            }
        }
    }

    const formatTimestamp = (timestamp: Date) => {
        return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    const renderMessage = (message: Message) => {
        const isUser = message.role === 'user'

        return (
            <div key={message.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                {!isUser && (
                    <Avatar className="w-8 h-8">
                        <AvatarImage src="/bot-avatar.png" alt="AI Assistant" />
                        <AvatarFallback className="bg-blue-100 text-blue-600">
                            <Bot className="w-4 h-4" />
                        </AvatarFallback>
                    </Avatar>
                )}

                <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
                    <Card className={`${isUser ? 'bg-blue-600 text-white' : 'bg-gray-50'}`}>
                        <CardContent className="p-3">
                            <div className="flex items-start justify-between gap-2">
                                <p
                                    className="text-sm leading-relaxed"
                                    {...(!isUser ? { 'data-testid': 'ai-response' } : {})}
                                >
                                    {message.content}
                                </p>
                                <span className={`text-xs ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                                    {formatTimestamp(message.timestamp)}
                                </span>
                            </div>

                            {message.metadata?.assessment && (
                                <div className="mt-2 pt-2 border-t border-gray-200">
                                    <div className="text-xs font-medium mb-1">Assessment Scores:</div>
                                    <div className="grid grid-cols-2 gap-1 text-xs">
                                        {Object.entries(message.metadata.assessment).map(([key, score]) => (
                                            <div key={key} className="flex justify-between">
                                                <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                                                <span className="font-medium">{score}/5</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {isUser && (
                    <Avatar className="w-8 h-8">
                        <AvatarImage src="/user-avatar.png" alt="User" />
                        <AvatarFallback className="bg-gray-100 text-gray-600">
                            <User className="w-4 h-4" />
                        </AvatarFallback>
                    </Avatar>
                )}
            </div>
        )
    }

    return (
        <div className={`flex flex-col h-full max-w-4xl mx-auto ${className}`}>
            {/* Header */}
            <Card className="mb-4">
                <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                            <CardTitle className="flex items-center gap-2">
                                <Bot className="w-5 h-5" />
                                AI System Design Learning Assistant
                            </CardTitle>
                        </div>
                        <Badge variant="secondary">
                            {messages.length} messages
                        </Badge>
                    </div>
                </CardHeader>
            </Card>

            {/* Messages */}
            <ScrollArea className="flex-1 mb-4 px-2">
                <div className="space-y-4">
                    {messages.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            <div className="text-4xl mb-4">🎯</div>
                            <h3 className="text-lg font-semibold mb-2">
                                Welcome to System Design Learning!
                            </h3>
                            <p className="text-sm mb-4">
                                Start a conversation to learn about system design concepts, architecture patterns, and best practices.
                            </p>
                            <div className="text-xs text-gray-400 space-y-1">
                                <p>💡 Try asking about:</p>
                                <p>• "How would you design a social media platform?"</p>
                                <p>• "What are the key components of a microservices architecture?"</p>
                                <p>• "How do you handle scalability in distributed systems?"</p>
                            </div>
                        </div>
                    ) : (
                        messages.map(renderMessage)
                    )}

                    {isTyping && (
                        <div className="flex gap-3 justify-start">
                            <Avatar className="w-8 h-8">
                                <AvatarFallback className="bg-blue-100 text-blue-600">
                                    <Bot className="w-4 h-4" />
                                </AvatarFallback>
                            </Avatar>
                            <Card className="bg-gray-50">
                                <CardContent className="p-3">
                                    <div className="flex items-center gap-1">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                        </div>
                                        <span className="text-sm text-gray-500 ml-2">AI is typing...</span>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </ScrollArea>

            {/* Error Display */}
            {error && (
                <Card className="mb-4 border-red-200 bg-red-50">
                    <CardContent className="p-3">
                        <div className="flex items-center gap-2 text-red-700">
                            <AlertCircle className="w-4 h-4" />
                            <span className="text-sm">{error}</span>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Input Form */}
            <Card>
                <CardContent className="p-6 pt-4">
                    <form onSubmit={handleSubmit} className="flex gap-2">
                        <Input
                            ref={inputRef}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about system design concepts, architecture patterns, or start drawing..."
                            disabled={isLoading || isSubmitting}
                            className="flex-1"
                            aria-label="Type your message"
                            data-testid="message-input"
                        />
                        <Button
                            type="submit"
                            disabled={!inputValue.trim() || isLoading || isSubmitting}
                            className="px-6"
                            data-testid="send-button"
                        >
                            <Send className="w-4 h-4 mr-2" />
                            Send
                        </Button>
                    </form>
                    <div className="text-xs text-gray-500 mt-2 text-center">
                        Press Enter to send, Shift+Enter for new line
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
