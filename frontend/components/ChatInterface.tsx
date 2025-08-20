'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar'
import { Badge } from './ui/badge'
import { ScrollArea } from './ui/scroll-area'
import { Separator } from './ui/separator'
import { Send, Bot, User, AlertCircle, Mic, Volume2 } from 'lucide-react'
import { AssessmentButton } from './AssessmentButton'
import { VoiceInterface } from './VoiceInterface'
import { useTheme } from '@/contexts/ThemeContext'

export interface Message {
    id: string
    content: string
    role: 'user' | 'assistant'
    timestamp: Date
    type?: 'text' | 'voice' | 'image'
    isStreaming?: boolean
    hasAudio?: boolean
    isLoading?: boolean
    isTyping?: boolean // For typing indicator
    imageData?: string // Base64 PNG data for images
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
    isAnalyzing?: boolean
    error?: null
    isTyping?: boolean
    className?: string
    showAssessmentButton?: boolean
    onVoiceTranscriptStart?: (role: 'user' | 'assistant') => void
    onVoiceTranscriptUpdate?: (transcript: string, role: 'user' | 'assistant') => void
    onVoiceTranscriptComplete?: (role: 'user' | 'assistant') => void
    sessionId?: string
}

export function ChatInterface({
    messages,
    onSendMessage,
    onRequestAssessment,
    isLoading = false,
    isAnalyzing = false,
    error = null,
    isTyping = false,
    className = '',
    showAssessmentButton = false,
    onVoiceTranscriptStart,
    onVoiceTranscriptUpdate,
    onVoiceTranscriptComplete,
    sessionId
}: ChatInterfaceProps) {
    const { theme } = useTheme()
    const [inputValue, setInputValue] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [selectedChapter, setSelectedChapter] = useState<string | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Get selected chapter from localStorage on mount
    useEffect(() => {
        const chapter = localStorage.getItem('selectedChapter')
        setSelectedChapter(chapter)
    }, [])

    // Get chapter-specific content
    const getChapterContent = () => {
        const chapterData: { [key: string]: { title: string; suggestions: string[] } } = {
            'twitter': {
                title: 'Design Twitter/X',
                suggestions: [
                    '• "Let\'s start with the core features of Twitter"',
                    '• "What are the main components we need?"',
                    '• "How do we handle millions of tweets per day?"'
                ]
            },
            'url-shortener': {
                title: 'URL Shortener (bit.ly)',
                suggestions: [
                    '• "How do we generate short URLs?"',
                    '• "What database design do we need?"',
                    '• "How do we handle analytics and tracking?"'
                ]
            },
            'chat-system': {
                title: 'Chat System (WhatsApp)',
                suggestions: [
                    '• "How do we ensure real-time message delivery?"',
                    '• "What about group chats and media sharing?"',
                    '• "How do we handle message encryption?"'
                ]
            },
            'newsfeed': {
                title: 'News Feed System',
                suggestions: [
                    '• "How do we generate personalized feeds?"',
                    '• "What about ranking and recommendation algorithms?"',
                    '• "How do we handle feed updates at scale?"'
                ]
            }
        }

        if (selectedChapter && chapterData[selectedChapter]) {
            return chapterData[selectedChapter]
        }

        return {
            title: 'System Design Interview',
            suggestions: [
                '• "Design a URL shortener like bit.ly"',
                '• "How would you scale a chat application?"',
                '• "Design a recommendation system"'
            ]
        }
    }

    const chapterContent = getChapterContent()
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
        if (!isLoading && !isAnalyzing && !isTyping) {
            setIsSubmitting(false)
        }
    }, [isLoading, isAnalyzing, isTyping])

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

    // Enhanced markdown renderer for images and text formatting
    const renderMessageContent = (content: string) => {
        const parts = []
        let lastIndex = 0
        
        // Combined regex for images and text formatting
        const markdownRegex = /(!?\[([^\]]*)\]\(([^)]+)\))|(\*\*([^*]+)\*\*)|(\*([^*]+)\*)|(`([^`]+)`)|(\n)/g
        let match

        while ((match = markdownRegex.exec(content)) !== null) {
            // Add text before the current match
            if (match.index > lastIndex) {
                const textContent = content.slice(lastIndex, match.index)
                if (textContent.trim()) {
                    parts.push(
                        <span key={`text-${lastIndex}`}>{textContent}</span>
                    )
                }
            }

            if (match[1]) {
                // Image syntax: ![alt](src)
                const [, , altText, src] = match
                parts.push(
                    <div key={`img-${match.index}`} className="my-3">
                        <img 
                            src={src} 
                            alt={altText} 
                            className="max-w-full h-auto rounded-lg shadow-md border border-gray-200"
                            style={{ maxHeight: '400px' }}
                        />
                        {altText && (
                            <p className="text-xs text-gray-500 mt-1 text-center italic">
                                {altText}
                            </p>
                        )}
                    </div>
                )
            } else if (match[4]) {
                // Bold syntax: **text**
                const boldText = match[5]
                parts.push(
                    <strong key={`bold-${match.index}`} className="font-bold">
                        {boldText}
                    </strong>
                )
            } else if (match[6]) {
                // Italic syntax: *text*
                const italicText = match[7]
                parts.push(
                    <em key={`italic-${match.index}`} className="italic">
                        {italicText}
                    </em>
                )
            } else if (match[8]) {
                // Code syntax: `text`
                const codeText = match[9]
                parts.push(
                    <code key={`code-${match.index}`} className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono">
                        {codeText}
                    </code>
                )
            } else if (match[10]) {
                // Line break
                parts.push(
                    <br key={`br-${match.index}`} />
                )
            }

            lastIndex = markdownRegex.lastIndex
        }

        // Add remaining text after the last match
        if (lastIndex < content.length) {
            const remainingContent = content.slice(lastIndex)
            if (remainingContent.trim()) {
                parts.push(
                    <span key={`text-${lastIndex}`}>{remainingContent}</span>
                )
            }
        }

        // If no markdown found, return the original content but with line breaks
        if (parts.length === 0) {
            return content.split('\n').map((line, index) => (
                <React.Fragment key={index}>
                    {index > 0 && <br />}
                    {line}
                </React.Fragment>
            ))
        }

        return parts
    }

    const renderMessage = (message: Message) => {
        const isUser = message.role === 'user'
        
        // Check if this message contains AI Design Review or Assessment (USP features)
        const isAIDesignReview = !isUser && (
            message.content.includes('AI Design Review') ||
            message.content.includes('COMPONENTS:') ||
            message.content.includes('FEEDBACK:') ||
            message.content.includes('SUGGESTIONS:') ||
            message.content.includes('Architectural feedback') ||
            message.content.includes('system design diagram')
        )
        const isAssessment = !isUser && (message.content.includes('Assessment Complete') || message.metadata?.assessment)
        const isUSPFeature = isAIDesignReview || isAssessment

        return (
            <div key={message.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} w-full`}>
                {!isUser && (
                    <Avatar className="w-8 h-8">
                        <AvatarImage src="/bot-avatar.png" alt="AI Assistant" />
                        <AvatarFallback className={isUSPFeature ? "bg-gradient-to-br from-purple-500 to-blue-600 text-white" : "bg-blue-100 text-blue-600"}>
                            <Bot className="w-4 h-4" />
                        </AvatarFallback>
                    </Avatar>
                )}

                <div className={`max-w-[80%] min-w-0 w-full ${isUser ? 'order-first' : ''}`}>
                    {/* USP Feature Badge */}
                    {isUSPFeature && (
                        <div className="mb-2 flex justify-center">
                            <Badge className={`text-xs font-medium px-2 py-1 ${
                                isAIDesignReview 
                                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white'
                                    : 'bg-gradient-to-r from-green-600 to-emerald-600 text-white'
                            }`}>
                                {isAIDesignReview ? '🎨 AI Design Review' : '📊 Assessment'}
                            </Badge>
                        </div>
                    )}
                    <Card className={`transition-all duration-200 w-full overflow-hidden ${
                        isUSPFeature
                            ? (theme === 'dark'
                                ? 'bg-gradient-to-br from-purple-900/30 to-blue-900/30 border-purple-500/50 text-purple-100 shadow-lg ring-1 ring-purple-400/30'
                                : 'bg-gradient-to-br from-purple-50 to-blue-50 border-purple-300 text-purple-900 shadow-lg ring-1 ring-purple-200'
                              )
                            : isUser 
                                ? (theme === 'dark'
                                    ? 'bg-slate-700 border-slate-600 text-white shadow-sm'
                                    : 'bg-slate-200 border-slate-300 text-slate-900 shadow-sm'
                                  )
                                : (theme === 'dark' 
                                    ? 'bg-gray-800 border-gray-700 text-gray-100 shadow-sm' 
                                    : 'bg-gray-50 border-gray-200 text-gray-900 shadow-sm'
                                  )
                    }`}>
                        <CardContent className="p-4 w-full overflow-hidden">
                            {/* Voice message header */}
                            {message.type === 'voice' && (
                                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-200">
                                    {message.role === 'user' ? (
                                        <Mic className={`w-4 h-4 ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`} />
                                    ) : (
                                        <Volume2 className={`w-4 h-4 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-500'}`} />
                                    )}
                                    <span className={`text-xs font-medium ${
                                        message.role === 'user' 
                                            ? (theme === 'dark' ? 'text-slate-300' : 'text-slate-600')
                                            : (theme === 'dark' ? 'text-blue-300' : 'text-blue-600')
                                    }`}>
                                        {message.role === 'user' ? 'Voice Message' : 'AI Voice Response'}
                                        {message.isStreaming && (
                                            <span className="ml-2 inline-flex items-center">
                                                <div className={`w-2 h-2 rounded-full animate-pulse mr-1 ${
                                                    message.role === 'user' 
                                                        ? (theme === 'dark' ? 'bg-slate-400' : 'bg-slate-500')
                                                        : (theme === 'dark' ? 'bg-blue-400' : 'bg-blue-500')
                                                }`} />
                                                {message.role === 'user' ? 'Speaking...' : 'AI Speaking...'}
                                            </span>
                                        )}
                                    </span>
                                </div>
                            )}
                            
                            <div className="flex items-start justify-between gap-2">
                                <div
                                    className="text-sm leading-relaxed chat-text-wrap flex-1 min-w-0"
                                    {...(!isUser ? { 'data-testid': 'ai-response' } : {})}
                                >
                                    {(() => {
                                        console.log('Message rendering check:', { 
                                            id: message.id, 
                                            type: message.type, 
                                            hasImageData: !!message.imageData,
                                            imageDataPrefix: message.imageData ? message.imageData.substring(0, 50) : 'none'
                                        })
                                        return message.type === 'image' && message.imageData
                                    })() ? (
                                        <div className="space-y-2">
                                            <img 
                                                src={message.imageData} 
                                                alt="Saved whiteboard design"
                                                className={`max-w-full h-auto rounded-lg shadow-sm ${
                                                    theme === 'dark' 
                                                        ? 'border border-gray-600' 
                                                        : 'border border-gray-200'
                                                }`}
                                                style={{ maxHeight: '300px' }}
                                                onLoad={() => console.log('Image loaded successfully for:', message.id)}
                                                onError={(e) => console.error('Image failed to load for:', message.id, e)}
                                            />
                                            {message.content && (
                                                <div className={`text-sm ${
                                                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                                                }`}>
                                                    {renderMessageContent(message.content)}
                                                </div>
                                            )}
                                        </div>
                                    ) : message.isTyping ? (
                                        // Animated typing indicator
                                        <div className="flex items-center gap-3 min-w-0">
                                            <span className="whitespace-nowrap text-sm">{message.content}</span>
                                            <div className="flex space-x-1 flex-shrink-0">
                                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                                            </div>
                                        </div>
                                    ) : (
                                        message.content ? renderMessageContent(message.content) : (message.isStreaming ? '...' : '')
                                    )}
                                </div>
                                <span className={`text-xs ${isUser ? (theme === 'dark' ? 'text-slate-400' : 'text-slate-500') : (theme === 'dark' ? 'text-gray-400' : 'text-gray-500')}`}>
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

    // Check if this is a demo session
    const isDemoSession = sessionId && ['twitter-clone-demo', 'session_2', 'session_3'].includes(sessionId)

    return (
        <div className={`flex flex-col h-full ${className}`}>
            {/* Demo Badge */}
            {isDemoSession && (
                <div className={`px-4 py-2 border-b ${theme === 'dark' ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'}`}>
                    <div className="flex items-center justify-center">
                        <Badge className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-medium px-3 py-1">
                            ✨ Demo Session - Showcasing Product Features
                        </Badge>
                    </div>
                </div>
            )}
            {/* Messages Area - Only this scrolls */}
            <ScrollArea ref={scrollAreaRef} className="flex-1 min-h-0 px-4">
                <div className="space-y-4 py-4">
                    {messages.length === 0 ? (
                        <div className={`text-center py-6 px-3 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                            <div className="text-3xl mb-3">👋</div>
                            <h3 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                                Welcome to your interview!
                            </h3>
                            <p className={`text-sm mb-3 leading-relaxed ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                                I'm your AI interviewer. {selectedChapter ? `Today we'll be working on: ${chapterContent.title}` : 'Let\'s simulate a real system design interview.'}
                            </p>
                            <div className={`rounded-lg p-3 mb-4 border ${
                                theme === 'dark' 
                                    ? 'bg-purple-900/20 border-purple-700/30' 
                                    : 'bg-purple-50 border-purple-200'
                            }`}>
                                <p className={`text-xs font-semibold mb-2 ${theme === 'dark' ? 'text-purple-300' : 'text-purple-800'}`}>
                                    🎯 Get detailed 6-dimensional scoring:
                                </p>
                                <div className={`grid grid-cols-2 gap-1 text-xs ${theme === 'dark' ? 'text-purple-200' : 'text-purple-700'}`}>
                                    <div>• Requirements</div>
                                    <div>• Architecture</div>
                                    <div>• Technical Deep Dive</div>
                                    <div>• Scalability</div>
                                    <div>• Reliability</div>
                                    <div>• Communication</div>
                                </div>
                            </div>
                            <p className={`text-sm mb-4 leading-relaxed ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                                Use the whiteboard to sketch your ideas as we discuss!
                            </p>
                            <div className={`rounded-xl p-3 border ${
                                theme === 'dark' 
                                    ? 'bg-gray-700 border-gray-600' 
                                    : 'bg-blue-50 border-blue-200'
                            }`}>
                                <p className={`text-xs font-medium mb-2 ${theme === 'dark' ? 'text-gray-200' : 'text-blue-800'}`}>💡 Let's begin with:</p>
                                <div className={`space-y-1 text-xs ${theme === 'dark' ? 'text-gray-300' : 'text-blue-700'}`}>
                                    {chapterContent.suggestions.map((suggestion, index) => (
                                        <p key={index}>{suggestion}</p>
                                    ))}
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
                                disabled={isLoading || isAnalyzing || isSubmitting}
                                className={`border-0 focus:ring-0 focus:outline-none text-base p-3 rounded-xl resize-none ${
                                    theme === 'dark' 
                                        ? 'bg-gray-600 text-white placeholder:text-gray-400' 
                                        : 'bg-gray-50 text-gray-900 placeholder:text-gray-500'
                                }`}
                                aria-label="Type your message"
                                data-testid="message-input"
                            />
                        </div>
                        <VoiceInterface 
                            inline 
                            onTranscriptStart={onVoiceTranscriptStart}
                            onTranscriptUpdate={onVoiceTranscriptUpdate}
                            onTranscriptComplete={onVoiceTranscriptComplete}
                        />
                        <Button
                            type="submit"
                            disabled={!inputValue.trim() || isLoading || isAnalyzing || isSubmitting}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-all duration-200 shadow-md hover:shadow-lg"
                            data-testid="send-button"
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </form>
                    <div className={`text-[10px] mt-3 text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
AI can make mistakes. Please verify important information and double-check responses.
                    </div>
                </div>
            </div>
        </div>
    )
}
