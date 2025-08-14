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
import { AssessmentButton } from './AssessmentButton'
import { VoiceInterface } from './VoiceInterface'
import { useTheme } from '@/contexts/ThemeContext'

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
    onRequestAssessment?: () => void
    isLoading?: boolean
    error?: null
    isTyping?: boolean
    className?: string
    showAssessmentButton?: boolean
}

export function ChatInterface({
    messages,
    onSendMessage,
    onRequestAssessment,
    isLoading = false,
    error = null,
    isTyping = false,
    className = '',
    showAssessmentButton = false
}: ChatInterfaceProps) {
    const { theme } = useTheme()
    const [inputValue, setInputValue] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const scrollAreaRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    const scrollToBottom = () => {
        if (scrollAreaRef.current) {
            const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
            if (scrollElement) {
                scrollElement.scrollTop = scrollElement.scrollHeight
            }
        }
    }

    useEffect(() => {
        // Only auto-scroll to bottom if there are messages
        if (messages.length > 0) {
            // Use setTimeout to ensure DOM has updated
            setTimeout(scrollToBottom, 100)
        }
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
                    <Card className={`transition-all duration-200 ${
                        isUser 
                            ? 'bg-blue-600 text-white shadow-lg' 
                            : (theme === 'dark' 
                                ? 'bg-gray-700 border-gray-600 text-white shadow-sm' 
                                : 'bg-white border-gray-200 shadow-sm'
                              )
                    }`}>
                        <CardContent className="p-4">
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
        <div className={`flex flex-col h-full ${className}`}>
            {/* Messages Area - Only this scrolls */}
            <ScrollArea ref={scrollAreaRef} className="flex-1 min-h-0 px-4">
                <div className="space-y-4 py-4">
                    {messages.length === 0 ? (
                        <div className={`text-center py-6 px-3 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                            <div className="text-3xl mb-3">👋</div>
                            <h3 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                                Welcome to your interview!
                            </h3>
                            <p className={`text-sm mb-4 leading-relaxed ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                                I'm your AI interviewer. Let's start by discussing a system design problem. Feel free to use the whiteboard to sketch your ideas!
                            </p>
                            <div className={`rounded-xl p-3 border ${
                                theme === 'dark' 
                                    ? 'bg-gray-700 border-gray-600' 
                                    : 'bg-blue-50 border-blue-200'
                            }`}>
                                <p className={`text-xs font-medium mb-2 ${theme === 'dark' ? 'text-gray-200' : 'text-blue-800'}`}>💡 Let's begin with:</p>
                                <div className={`space-y-1 text-xs ${theme === 'dark' ? 'text-gray-300' : 'text-blue-700'}`}>
                                    <p>• "Design a URL shortener like bit.ly"</p>
                                    <p>• "How would you scale a chat application?"</p>
                                    <p>• "Design a recommendation system"</p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <>
                            {messages.map(renderMessage)}

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

                            {/* Assessment Button - Show after some messages or when explicitly enabled */}
                            {((messages.length >= 2 && onRequestAssessment) || (showAssessmentButton && onRequestAssessment && messages.length > 0)) && (
                                <div className="flex justify-center py-4">
                                    <div className="text-center">
                                        <p className="text-sm text-gray-600 mb-3">
                                            Ready to evaluate your progress?
                                        </p>
                                        <AssessmentButton onRequestAssessment={onRequestAssessment} />
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </>
                    )}
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
            <div className="flex-shrink-0 px-4 pb-4">
                <div className={`rounded-2xl shadow-lg p-3 border ${
                    theme === 'dark' 
                        ? 'bg-gray-700 border-gray-600' 
                        : 'bg-white border-gray-200'
                }`}>
                    <form onSubmit={handleSubmit} className="flex gap-2 items-end">
                        <div className="flex-1">
                            <Input
                                ref={inputRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Discuss your approach, ask clarifying questions..."
                                disabled={isLoading || isSubmitting}
                                className={`border-0 focus:ring-0 focus:outline-none text-base p-3 rounded-xl resize-none ${
                                    theme === 'dark' 
                                        ? 'bg-gray-600 text-white placeholder:text-gray-400' 
                                        : 'bg-gray-50 text-gray-900 placeholder:text-gray-500'
                                }`}
                                aria-label="Type your message"
                                data-testid="message-input"
                            />
                        </div>
                        <VoiceInterface inline />
                        <Button
                            type="submit"
                            disabled={!inputValue.trim() || isLoading || isSubmitting}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-all duration-200 shadow-md hover:shadow-lg"
                            data-testid="send-button"
                        >
                            <Send className="w-4 h-4 mr-2" />
                            Send
                        </Button>
                    </form>
                    <div className={`text-xs mt-3 text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                        Press Enter to send, Shift+Enter for new line
                    </div>
                </div>
            </div>
        </div>
    )
}
