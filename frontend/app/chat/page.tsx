'use client'

import { useState, useEffect } from 'react'
import { ChatInterface } from '../../components/ChatInterface'
import { WhiteboardCanvas } from '../../components/WhiteboardCanvas'
import { VoiceInterface } from '../../components/VoiceInterface'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { ChevronLeft, ChevronRight, MessageSquare, Palette, Target, X } from 'lucide-react'
import { AssessmentPanel } from '../../components/AssessmentPanel'

interface Message {
    id: string
    content: string
    role: 'user' | 'assistant'
    timestamp: Date
}

interface AnalysisResult {
    components_identified: string[]
    architectural_feedback: string
    suggestions: string[]
    confidence_score: number
    cost_estimate?: number
    tokens_used?: number
    raw_analysis?: string
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [whiteboardVisible, setWhiteboardVisible] = useState(true)
    const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [showFeedback, setShowFeedback] = useState(false)
    const [assessmentResult, setAssessmentResult] = useState<any>(null)
    const [isAssessmentLoading, setIsAssessmentLoading] = useState(false)


    // Mock user for development
    const mockUser = { email: 'john@example.com' }

    useEffect(() => {
        // Load session ID from localStorage
        const savedSessionId = localStorage.getItem(`sessionId:${mockUser.email}`)
        if (savedSessionId) {
            setSessionId(savedSessionId)
        }
    }, [mockUser.email])

    useEffect(() => {
        // Save session ID to localStorage when it changes
        if (sessionId) {
            localStorage.setItem(`sessionId:${mockUser.email}`, sessionId)
        }
    }, [sessionId, mockUser.email])

    const handleSendMessage = async (message: string) => {
        if (!message.trim()) return

        const userMessage: Message = {
            id: Date.now().toString(),
            content: message,
            role: 'user',
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setIsLoading(true)

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: mockUser.email,
                    session_id: sessionId
                }),
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const data = await response.json()

            // Extract session ID from response if provided
            if (data.session_id && data.session_id !== sessionId) {
                setSessionId(data.session_id)
            }

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: data.message,  // Backend returns 'message', not 'response'
                role: 'assistant',
                timestamp: new Date()
            }

            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            console.error('Failed to send message:', error)
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: 'Sorry, I encountered an error. Please try again.',
                role: 'assistant',
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setIsLoading(false)
        }
    }

    const handleWhiteboardSave = async (pngData: string) => {
        try {
            setIsLoading(true)
            const response = await fetch('/api/whiteboard/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    png_data: pngData,
                    user_id: mockUser.email || 'web_user',
                    session_id: sessionId || undefined,
                    description: 'System design whiteboard diagram'
                }),
            })
            if (!response.ok) {
                let errText = `Upload failed (${response.status})`
                try { const errJson = await response.json(); errText = errJson?.detail || errJson?.message || errText; } catch (_) { }
                throw new Error(errText)
            }
            const data = await response.json()
            console.log('PNG uploaded successfully:', data.artifact_id)
            alert(`Whiteboard saved successfully! Artifact ID: ${data.artifact_id}`)
        } catch (error) {
            console.error('Failed to upload PNG:', error)
            alert(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
        } finally {
            setIsLoading(false)
        }
    }

    const handleWhiteboardAnalysis = async (pngData: string) => {
        try {
            setIsAnalyzing(true)
            setShowFeedback(true)

            // First, upload the PNG to get an artifact ID
            const uploadResponse = await fetch('/api/whiteboard/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    png_data: pngData,
                    user_id: mockUser.email || 'web_user',
                    session_id: sessionId || undefined,
                    description: 'System design whiteboard diagram for analysis'
                }),
            })

            if (!uploadResponse.ok) {
                let errText = `Upload failed (${uploadResponse.status})`
                try { const errJson = await uploadResponse.json(); errText = errJson?.detail || errJson?.message || errText; } catch (_) { }
                throw new Error(errText)
            }

            const uploadData = await uploadResponse.json()
            const artifactId = uploadData.artifact_id

            // Now analyze the uploaded artifact
            const analysisResponse = await fetch('/api/whiteboard/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    artifact_id: artifactId,
                    user_id: mockUser.email || 'web_user',
                    session_id: sessionId || undefined,
                    analysis_type: 'comprehensive'
                }),
            })

            if (!analysisResponse.ok) {
                let errText = `Analysis failed (${analysisResponse.status})`
                try { const errJson = await analysisResponse.json(); errText = errJson?.detail || errJson?.message || errText; } catch (_) { }
                throw new Error(errText)
            }

            const analysisData = await analysisResponse.json()
            setAnalysisResult(analysisData)
            console.log('Analysis completed:', analysisData)
        } catch (error) {
            console.error('Failed to analyze whiteboard:', error)
            alert(`Analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
        } finally {
            setIsAnalyzing(false)
        }
    }

    const toggleWhiteboard = () => {
        setWhiteboardVisible(!whiteboardVisible)
    }

    const closeFeedback = () => {
        setShowFeedback(false)
        setAnalysisResult(null)
    }

    const handleRequestAssessment = async () => {
        if (messages.length < 2) return

        setIsAssessmentLoading(true)

        try {
            // Prepare assessment request data
            const conversationHistory = messages
                .map(msg => `${msg.role}: ${msg.content}`)
                .join('\n')
                .slice(-2000) // Limit to last 2000 characters

            const assessmentRequest = {
                user_id: mockUser.email,
                interaction_context: `User engaged in system design learning session with ${messages.length} messages exchanged. Recent conversation: ${messages.slice(-3).map(m => m.content).join(' ')}`,
                conversation_history: conversationHistory,
                assessment_type: 'chat'
            }

            const response = await fetch('/api/assessment/evaluate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(assessmentRequest),
            })

            if (!response.ok) {
                throw new Error(`Assessment failed: ${response.status}`)
            }

            const assessmentData = await response.json()
            setAssessmentResult(assessmentData)

            // Switch to assessment tab to show results
            setWhiteboardVisible(false)

        } catch (error) {
            console.error('Failed to get assessment:', error)
            alert(`Assessment failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
        } finally {
            setIsAssessmentLoading(false)
        }
    }



    return (
        <div className="flex h-screen bg-gray-50">
            {/* Chat Panel - Left Side */}
            <div className={`flex flex-col transition-all duration-300 ease-in-out ${whiteboardVisible ? 'w-[45%]' : 'w-full'
                }`}>
                <div className="flex-1 p-6 overflow-hidden">
                    <div className="h-full flex flex-col">
                        <div className="flex items-center justify-between mb-6">
                            <h1 className="text-2xl font-bold text-gray-900">System Design AI Tutor</h1>
                            <Button
                                onClick={toggleWhiteboard}
                                variant="outline"
                                size="sm"
                                className="flex items-center gap-2"
                            >
                                {whiteboardVisible ? (
                                    <>
                                        <ChevronRight className="h-4 w-4" />
                                        Hide Whiteboard
                                    </>
                                ) : (
                                    <>
                                        <ChevronLeft className="h-4 w-4" />
                                        Show Whiteboard
                                    </>
                                )}
                            </Button>
                        </div>

                        <div className="flex-1 overflow-hidden">
                            <div className="mb-4">
                                <VoiceInterface />
                            </div>
                            <ChatInterface
                                messages={messages}
                                onSendMessage={handleSendMessage}
                                onRequestAssessment={handleRequestAssessment}
                                isLoading={isLoading}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Whiteboard Panel - Right Side */}
            {whiteboardVisible && (
                <div className="w-[55%] border-l border-gray-200 bg-white">
                    <div className="h-full flex flex-col">
                        <div className="flex items-center justify-between p-4 border-b border-gray-200">
                            <div className="flex items-center gap-2">
                                <Palette className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">System Design Whiteboard</h2>
                            </div>
                        </div>

                        <div className="flex-1 overflow-hidden p-4">
                            <WhiteboardCanvas
                                onSave={handleWhiteboardSave}
                                onAnalyze={handleWhiteboardAnalysis}
                                isAnalyzing={isAnalyzing}
                            />
                        </div>
                    </div>
                </div>
            )}



            {/* Assessment Panel */}
            {!whiteboardVisible && assessmentResult && (
                <div className="flex-1 bg-white border-l border-gray-200">
                    <div className="h-full flex flex-col">
                        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-purple-50">
                            <div className="flex items-center gap-2">
                                <Target className="h-5 w-5 text-purple-600" />
                                <h2 className="text-lg font-semibold text-gray-900">Learning Assessment</h2>
                            </div>
                            <Button
                                onClick={() => setWhiteboardVisible(true)}
                                variant="outline"
                                size="sm"
                                className="flex items-center gap-2"
                            >
                                <ChevronLeft className="h-4 w-4" />
                                Back to Whiteboard
                            </Button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4">
                            <AssessmentPanel assessment={assessmentResult} />
                        </div>
                    </div>
                </div>
            )}

            {/* Feedback Panel - Overlay */}
            {showFeedback && analysisResult && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <Card className="w-[90%] max-w-4xl max-h-[90vh] overflow-hidden">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                            <div className="flex items-center gap-2">
                                <Target className="h-5 w-5 text-green-600" />
                                <CardTitle>Design Analysis Results</CardTitle>
                            </div>
                            <Button
                                onClick={closeFeedback}
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>

                        <CardContent className="space-y-6 overflow-y-auto max-h-[70vh]">
                            {/* Components Identified */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="space-y-3">
                                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                        <MessageSquare className="h-4 w-4 text-blue-600" />
                                        Components Identified
                                    </h3>
                                    <div className="bg-blue-50 rounded-lg p-3">
                                        <ul className="space-y-1 text-sm text-blue-800">
                                            {analysisResult.components_identified.map((component, index) => (
                                                <li key={index} className="flex items-center gap-2">
                                                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                                                    {component}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                        <Target className="h-4 w-4 text-green-600" />
                                        Architectural Feedback
                                    </h3>
                                    <div className="bg-green-50 rounded-lg p-3">
                                        <p className="text-sm text-green-800">
                                            {analysisResult.architectural_feedback}
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                        <Palette className="h-4 w-4 text-purple-600" />
                                        Suggestions
                                    </h3>
                                    <div className="bg-purple-50 rounded-lg p-3">
                                        <ul className="space-y-1 text-sm text-purple-800">
                                            {analysisResult.suggestions.map((suggestion, index) => (
                                                <li key={index} className="flex items-center gap-2">
                                                    <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                                                    {suggestion}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            {/* Analysis Metrics */}
                            <div className="border-t border-gray-200 pt-4">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-blue-600">
                                            {Math.round(analysisResult.confidence_score * 100)}%
                                        </div>
                                        <div className="text-sm text-gray-600">Confidence Score</div>
                                    </div>

                                    {analysisResult.cost_estimate && (
                                        <div className="text-center">
                                            <div className="text-2xl font-bold text-green-600">
                                                ${analysisResult.cost_estimate.toFixed(4)}
                                            </div>
                                            <div className="text-sm text-gray-600">Estimated Cost</div>
                                        </div>
                                    )}

                                    {analysisResult.tokens_used && (
                                        <div className="text-center">
                                            <div className="text-2xl font-bold text-purple-600">
                                                {analysisResult.tokens_used.toLocaleString()}
                                            </div>
                                            <div className="text-sm text-gray-600">Tokens Used</div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Raw Analysis (Collapsible) */}
                            {analysisResult.raw_analysis && (
                                <div className="border-t border-gray-200 pt-4">
                                    <details className="group">
                                        <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                                            View Raw Analysis
                                        </summary>
                                        <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                                            <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                                                {analysisResult.raw_analysis}
                                            </pre>
                                        </div>
                                    </details>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    )
}
