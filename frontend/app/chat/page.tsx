'use client'

import React, { useState, useEffect, useRef } from 'react'
import { ChatInterface } from '../../components/ChatInterface'
import { WhiteboardCanvas } from '../../components/WhiteboardCanvas'
import { LearnInterface } from '../../components/LearnInterface'
import { Sidebar } from '../../components/Sidebar'
import { Button } from "../../components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs"
import { ChevronRight } from 'lucide-react'
import { demoSessions, DemoSessionId } from '../../data/demoSessions'
import { useTheme } from '../../contexts/ThemeContext'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  type?: 'text' | 'voice'
  isStreaming?: boolean
  hasAudio?: boolean
}

interface AssessmentResult {
  overall_score: number
  dimension_scores: {
    requirements_analysis: number
    system_architecture: number
    technical_deep_dive: number
    scale_performance: number
    reliability_fault_tolerance: number
    communication_thought_process: number
  }
  feedback: string
  strengths: string[]
  improvement_areas: string[]
}

export default function ChatPage() {
  const { theme } = useTheme()
  const [messages, setMessages] = useState<Message[]>([])
  const [sessionId, setSessionId] = useState<string>('')
  const [sessions, setSessions] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResult | null>(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [mobileActivePanel, setMobileActivePanel] = useState<'chat' | 'learn' | 'whiteboard'>('chat')
  const [currentUserVoiceMessage, setCurrentUserVoiceMessage] = useState<Message | null>(null)
  const [currentAssistantVoiceMessage, setCurrentAssistantVoiceMessage] = useState<Message | null>(null)
  const currentUserVoiceMessageId = useRef<string | null>(null)
  const currentAssistantVoiceMessageId = useRef<string | null>(null)
  const [activeTab, setActiveTab] = useState<'learn' | 'practice'>('practice')
  const [selectedModule, setSelectedModule] = useState<string | null>(null)
  const [whiteboardClearTrigger, setWhiteboardClearTrigger] = useState(0)

  const userId = 'john@example.com' // This would come from auth context

  useEffect(() => {
    // Check if mobile
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    // Load existing session from localStorage
    const existingSessionId = localStorage.getItem(`sessionId:${userId}`)
    if (existingSessionId && !(existingSessionId in demoSessions)) {
      // Only load non-demo sessions as main sessions
      setSessionId(existingSessionId)
      setMainSessionId(existingSessionId) // Set as main session
      // Load session messages from localStorage
      const savedMessages = localStorage.getItem(`messages:${existingSessionId}`)
      if (savedMessages) {
        try {
          const parsedMessages = JSON.parse(savedMessages).map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
          setMessages(parsedMessages)
        } catch (error) {
          console.error('Failed to parse saved messages:', error)
        }
      }
    } else {
      // Generate new session ID if no valid session exists or if stored session is a demo
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setSessionId(newSessionId)
      setMainSessionId(newSessionId) // Set as main session
      localStorage.setItem(`sessionId:${userId}`, newSessionId)
    }

    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Track the main working session ID (doesn't change when browsing demo sessions)
  const [mainSessionId, setMainSessionId] = useState<string>('')
  
  // Load sessions list when sessionId or mainSessionId changes
  useEffect(() => {
    if (sessionId) {
      loadSessions()
    }
  }, [sessionId, mainSessionId])

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      localStorage.setItem(`messages:${sessionId}`, JSON.stringify(messages))
    }
  }, [messages, sessionId])

  const loadSessions = async () => {
    // Mock sessions for development - filter out mainSessionId from other sessions to avoid duplicates
    const otherSessions = [
      {
        id: 'twitter-clone-demo',
        title: 'Design Twitter Clone',
        created_at: '2025-08-13T10:00:00Z',
        message_count: 15
      },
      {
        id: 'session_2',
        title: 'Chat System Architecture',
        created_at: '2025-08-12T14:30:00Z',
        message_count: 22
      },
      {
        id: 'session_3',
        title: 'E-commerce Platform',
        created_at: '2025-08-11T09:15:00Z',
        message_count: 18
      }
    ].filter(session => session.id !== (mainSessionId || sessionId))

    const mockSessions = [
      {
        id: `current_session_${mainSessionId || sessionId}`, // Use unique prefix
        title: 'Current Session',
        created_at: new Date().toISOString(),
        message_count: messages.length,
        isCurrentSession: true // Flag to identify this as the current session
      },
      ...otherSessions
    ]
    setSessions(mockSessions)
  }

  const handleNewSession = () => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setSessionId(newSessionId)
    setMainSessionId(newSessionId) // Update main session
    setMessages([])
    setAssessmentResult(null)
    setWhiteboardClearTrigger(prev => prev + 1) // Trigger whiteboard clear
    localStorage.setItem(`sessionId:${userId}`, newSessionId)
    localStorage.removeItem(`messages:${sessionId}`) // Clear old session messages
    loadSessions()
  }

  const handleSelectSession = (selectedSessionId: string) => {
    // Check if this is the current session (with the new prefix format)
    const isCurrentSession = selectedSessionId.startsWith('current_session_')
    
    // Early return if selecting the current session - don't clear anything
    if (selectedSessionId === sessionId || isCurrentSession) {
      // If it's the current session but we're viewing a different session, switch back to main
      if (isCurrentSession && sessionId !== mainSessionId) {
        setSessionId(mainSessionId)
        // Load main session messages
        const savedMessages = localStorage.getItem(`messages:${mainSessionId}`)
        if (savedMessages) {
          try {
            const parsedMessages = JSON.parse(savedMessages).map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp)
            }))
            setMessages(parsedMessages)
          } catch (error) {
            console.error('Failed to parse saved messages:', error)
            setMessages([])
          }
        } else {
          setMessages([])
        }
        setAssessmentResult(null)
      }
      return
    }
    
    // Save current session messages before switching
    if (messages.length > 0) {
      localStorage.setItem(`messages:${sessionId}`, JSON.stringify(messages))
    }
    
    setSessionId(selectedSessionId)
    setAssessmentResult(null)
    
    // Check if this is a demo session
    if (selectedSessionId in demoSessions) {
      // Don't update localStorage for demo sessions - keep the main session as the stored session
      const demoSession = demoSessions[selectedSessionId as DemoSessionId]
      setMessages(demoSession.messages)
      return
    }
    
    // Only update localStorage for non-demo sessions
    localStorage.setItem(`sessionId:${userId}`, selectedSessionId)
    
    // Load messages for regular sessions from localStorage
    const savedMessages = localStorage.getItem(`messages:${selectedSessionId}`)
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages).map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
        setMessages(parsedMessages)
      } catch (error) {
        console.error('Failed to parse saved messages:', error)
        setMessages([])
      }
    } else {
      setMessages([])
    }
  }

  // Voice message handling functions
  const handleVoiceTranscriptStart = (role: 'user' | 'assistant') => {
    const voiceMessage: Message = {
      id: `voice_${role}_${Date.now()}`,
      content: '',
      role: role,
      timestamp: new Date(),
      type: 'voice',
      isStreaming: true,
      hasAudio: role === 'assistant' // Only assistant messages have audio playback
    }
    
    if (role === 'user') {
      currentUserVoiceMessageId.current = voiceMessage.id
      setCurrentUserVoiceMessage(voiceMessage)
    } else {
      currentAssistantVoiceMessageId.current = voiceMessage.id
      setCurrentAssistantVoiceMessage(voiceMessage)
    }
    
    setMessages(prev => [...prev, voiceMessage])
  }

  const handleVoiceTranscriptUpdate = (transcript: string, role: 'user' | 'assistant') => {
    const messageId = role === 'user' ? currentUserVoiceMessageId.current : currentAssistantVoiceMessageId.current
    
    if (messageId) {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, content: transcript }
            : msg
        )
      )
      // Update current voice message state as well for consistency
      if (role === 'user') {
        setCurrentUserVoiceMessage(prev => 
          prev ? { ...prev, content: transcript } : prev
        )
      } else {
        setCurrentAssistantVoiceMessage(prev => 
          prev ? { ...prev, content: transcript } : prev
        )
      }
    }
  }

  const handleVoiceTranscriptComplete = (role: 'user' | 'assistant') => {
    const messageId = role === 'user' ? currentUserVoiceMessageId.current : currentAssistantVoiceMessageId.current
    
    if (messageId) {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, isStreaming: false }
            : msg
        )
      )
      
      // Reset current message tracking for this role
      if (role === 'user') {
        setCurrentUserVoiceMessage(null)
        currentUserVoiceMessageId.current = null
      } else {
        setCurrentAssistantVoiceMessage(null)
        currentAssistantVoiceMessageId.current = null
      }
    }
  }

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
          message,
          session_id: sessionId,
          user_id: userId
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()
      
      // Update session ID if provided
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id)
        localStorage.setItem(`sessionId:${userId}`, data.session_id)
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.message,
        role: 'assistant',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, aiMessage])
      loadSessions() // Refresh sessions list
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      alert('Failed to send message. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRequestAssessment = async () => {
    if (messages.length === 0) {
      alert('Please have a conversation first before requesting an assessment.')
      return
    }

    setIsLoading(true)

    try {
      // Format the conversation history as a string
      const conversationHistory = messages
        .map(msg => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`)
        .join('\n\n')
      
      // Create interaction context summary
      const interactionContext = `System design conversation with ${messages.length} messages. User practiced system design concepts with AI tutor.`
      
      const response = await fetch('/api/assessment/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          interaction_context: interactionContext,
          conversation_history: conversationHistory,
          assessment_type: "system_design"
        }),
      })

      if (!response.ok) {
        throw new Error('Assessment failed')
      }

      const result = await response.json()
      setAssessmentResult(result)
      
      // Format recommendations for display
      const recommendations = result.recommendations?.join('\n• ') || 'No specific recommendations available'
      const nextSteps = result.next_steps?.join('\n• ') || 'No specific next steps provided'
      
      // Add assessment result as a message
      const assessmentMessage: Message = {
        id: (Date.now() + 2).toString(),
        content: `🎯 **Assessment Complete**\n\n**Overall Score:** ${result.overall_score}/5.0 (Confidence: ${result.confidence_score}/5.0)\n\n**Summary:** ${result.summary}\n\n**Detailed Feedback:** ${result.detailed_feedback}\n\n**Recommendations:**\n• ${recommendations}\n\n**Next Steps:**\n• ${nextSteps}`,
        role: 'assistant',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assessmentMessage])
    } catch (error) {
      console.error('Assessment failed:', error)
      alert('Assessment failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleWhiteboardSave = async (pngData: string) => {
    try {
      const response = await fetch('/api/whiteboard/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          png_data: pngData,
          session_id: sessionId,
          user_id: userId
        }),
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()
      console.log('Whiteboard saved:', result.artifact_id)
      alert('Whiteboard saved successfully!')
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Please try again.')
    }
  }

  const handleWhiteboardAnalyze = async (pngData: string) => {
    setIsAnalyzing(true)

    try {
      // First upload the PNG
      const uploadResponse = await fetch('/api/whiteboard/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          png_data: pngData,
          session_id: sessionId,
          user_id: userId
        }),
      })

      if (!uploadResponse.ok) {
        throw new Error('Upload failed')
      }

      const uploadResult = await uploadResponse.json()

      // Then analyze the uploaded image
      const analyzeResponse = await fetch('/api/whiteboard/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          artifact_id: uploadResult.artifact_id,
          session_id: sessionId,
          user_id: userId
        }),
      })

      if (!analyzeResponse.ok) {
        throw new Error('Analysis failed')
      }

      const analysisResult = await analyzeResponse.json()
      
      // Add analysis result as a message
      const analysisMessage: Message = {
        id: (Date.now() + 3).toString(),
        content: `🔍 **Whiteboard Analysis**\n\n**Components Identified:** ${analysisResult.components_identified.join(', ')}\n\n**Feedback:** ${analysisResult.architectural_feedback}\n\n**Suggestions:** ${analysisResult.suggestions.join(', ')}\n\n**Confidence Score:** ${(analysisResult.confidence_score * 100).toFixed(1)}%`,
        role: 'assistant',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, analysisMessage])
    } catch (error) {
      console.error('Analysis failed:', error)
      alert('Analysis failed. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleSwipeLeft = () => {
    if (isMobile) {
      if (mobileActivePanel === 'chat') {
        setMobileActivePanel('learn')
      } else if (mobileActivePanel === 'learn') {
        setMobileActivePanel('whiteboard')
      }
    }
  }

  const handleSwipeRight = () => {
    if (isMobile) {
      if (mobileActivePanel === 'whiteboard') {
        setMobileActivePanel('learn')
      } else if (mobileActivePanel === 'learn') {
        setMobileActivePanel('chat')
      }
    }
  }

  return (
    <div className={`h-screen flex overflow-hidden ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        currentSessionId={sessionId}
        mainSessionId={mainSessionId}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        onModuleSelect={(moduleId) => {
          setSelectedModule(moduleId)
          setActiveTab('learn')
        }}
        selectedModule={selectedModule}
      />

      {/* Expand Button for Collapsed Sidebar */}
      {isSidebarCollapsed && (
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSidebarCollapsed(false)}
            className={`absolute top-4 left-2 z-10 p-1 h-8 w-8 rounded-lg shadow-lg ${
              theme === 'dark' 
                ? 'bg-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-700 border border-gray-600' 
                : 'bg-white text-gray-600 hover:text-gray-900 hover:bg-gray-100 border border-gray-200'
            }`}
            title="Expand sidebar"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {isMobile ? (
          /* Mobile: Single panel with swipe navigation */
          <div className="flex-1 relative">
            {/* Mobile Panel Indicators */}
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 flex space-x-1">
              <button
                onClick={() => setMobileActivePanel('chat')}
                className={`px-2 py-1 text-xs rounded-full transition-colors ${
                  mobileActivePanel === 'chat'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setMobileActivePanel('learn')}
                className={`px-2 py-1 text-xs rounded-full transition-colors ${
                  mobileActivePanel === 'learn'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Learn
              </button>
              <button
                onClick={() => setMobileActivePanel('whiteboard')}
                className={`px-2 py-1 text-xs rounded-full transition-colors ${
                  mobileActivePanel === 'whiteboard'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Design
              </button>
            </div>

            {/* Mobile Chat Panel */}
            <div
              className={`absolute inset-0 transition-transform duration-300 ${
                mobileActivePanel === 'chat' ? 'translate-x-0' : 
                mobileActivePanel === 'learn' ? '-translate-x-full' : '-translate-x-[200%]'
              }`}
              onTouchStart={(e) => {
                const touchStart = e.touches[0].clientX
                const handleTouchEnd = (endEvent: TouchEvent) => {
                  const touchEnd = endEvent.changedTouches[0].clientX
                  const diff = touchStart - touchEnd
                  if (diff > 50) handleSwipeLeft()
                  document.removeEventListener('touchend', handleTouchEnd)
                }
                document.addEventListener('touchend', handleTouchEnd)
              }}
            >
              <div className="h-full pt-16">
                <ChatInterface
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  onRequestAssessment={handleRequestAssessment}
                  isLoading={isLoading}
                  showAssessmentButton={true}
                  onVoiceTranscriptStart={handleVoiceTranscriptStart}
                  onVoiceTranscriptUpdate={handleVoiceTranscriptUpdate}
                  onVoiceTranscriptComplete={handleVoiceTranscriptComplete}
                  sessionId={sessionId}
                />
              </div>
            </div>

            {/* Mobile Learn Panel */}
            <div
              className={`absolute inset-0 transition-transform duration-300 ${
                mobileActivePanel === 'learn' ? 'translate-x-0' : 
                mobileActivePanel === 'chat' ? 'translate-x-full' : '-translate-x-full'
              }`}
              onTouchStart={(e) => {
                const touchStart = e.touches[0].clientX
                const handleTouchEnd = (endEvent: TouchEvent) => {
                  const touchEnd = endEvent.changedTouches[0].clientX
                  const diff = touchEnd - touchStart
                  if (diff > 50) handleSwipeRight()
                  if (diff < -50) handleSwipeLeft()
                  document.removeEventListener('touchend', handleTouchEnd)
                }
                document.addEventListener('touchend', handleTouchEnd)
              }}
            >
              <div className="h-full pt-16">
                <LearnInterface 
                  selectedModule={selectedModule}
                  onModuleSelect={setSelectedModule}
                />
              </div>
            </div>

            {/* Mobile Whiteboard Panel */}
            <div
              className={`absolute inset-0 transition-transform duration-300 ${
                mobileActivePanel === 'whiteboard' ? 'translate-x-0' : 
                mobileActivePanel === 'learn' ? 'translate-x-full' : 'translate-x-[200%]'
              }`}
              onTouchStart={(e) => {
                const touchStart = e.touches[0].clientX
                const handleTouchEnd = (endEvent: TouchEvent) => {
                  const touchEnd = endEvent.changedTouches[0].clientX
                  const diff = touchEnd - touchStart
                  if (diff > 50) handleSwipeRight()
                  document.removeEventListener('touchend', handleTouchEnd)
                }
                document.addEventListener('touchend', handleTouchEnd)
              }}
            >
              <div className="h-full pt-16">
                <WhiteboardCanvas
                  onSave={handleWhiteboardSave}
                  onAnalyze={handleWhiteboardAnalyze}
                  isAnalyzing={isAnalyzing}
                  clearTrigger={whiteboardClearTrigger}
                />
              </div>
            </div>
          </div>
        ) : (
          /* Desktop: Video Interview Layout - Main Area (75%), Interviewer Panel (25%) */
          <>
            {/* Primary Content Area (75%) */}
            <div className={`flex flex-col transition-all duration-300 ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`} 
                 style={{ flexBasis: '75%' }}>
              <div className="h-full p-4">
                <div className={`h-full rounded-2xl shadow-2xl overflow-hidden ${
                  theme === 'dark' 
                    ? 'bg-gray-800 ring-1 ring-gray-700' 
                    : 'bg-white ring-1 ring-gray-200'
                }`}>
                  <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'learn' | 'practice')} className="h-full flex flex-col">
                    {/* Tab Navigation */}
                    <div className={`px-6 pt-4 pb-3 border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
                      <div className="flex flex-col items-center space-y-3">
                        <TabsList className={`grid w-80 grid-cols-2 ${
                          theme === 'dark' 
                            ? 'bg-gray-700 text-gray-300' 
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          <TabsTrigger 
                            value="learn" 
                            className={`${
                              theme === 'dark' 
                                ? 'data-[state=active]:bg-gray-600 data-[state=active]:text-white' 
                                : 'data-[state=active]:bg-white data-[state=active]:text-gray-900'
                            }`}
                          >
                            📚 Learn
                          </TabsTrigger>
                          <TabsTrigger 
                            value="practice" 
                            className={`${
                              theme === 'dark' 
                                ? 'data-[state=active]:bg-gray-600 data-[state=active]:text-white' 
                                : 'data-[state=active]:bg-white data-[state=active]:text-gray-900'
                            }`}
                          >
                            🎯 Practice
                          </TabsTrigger>
                        </TabsList>
                        
                        {/* Tab Descriptions */}
                        <div className="text-center">
                          {activeTab === 'learn' ? (
                            <p className={`text-sm ${
                              theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                            }`}>
                              Interactive tutorials with notes, videos, and audio lessons
                            </p>
                          ) : (
                            <p className={`text-sm ${
                              theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                            }`}>
                              Design system architectures and get AI-powered feedback
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Tab Content */}
                    <TabsContent value="learn" className="flex-1 mt-0 h-full overflow-hidden">
                      <LearnInterface 
                        selectedModule={selectedModule}
                        onModuleSelect={setSelectedModule}
                      />
                    </TabsContent>

                    <TabsContent value="practice" className="flex-1 mt-0 h-full overflow-hidden">
                      <WhiteboardCanvas
                        onSave={handleWhiteboardSave}
                        onAnalyze={handleWhiteboardAnalyze}
                        isAnalyzing={isAnalyzing}
                        clearTrigger={whiteboardClearTrigger}
                      />
                    </TabsContent>
                  </Tabs>
                </div>
              </div>
            </div>

            {/* Interviewer Panel (25%) */}
            <div className={`flex flex-col transition-all duration-300 ${
              theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
            }`} style={{ flexBasis: '25%', minWidth: '400px' }}>
              <div className="h-full p-4">
                {/* Video Call Style Panel */}
                <div className={`h-full flex flex-col rounded-2xl shadow-2xl overflow-hidden ${
                  theme === 'dark' 
                    ? 'bg-gray-800 ring-1 ring-gray-700' 
                    : 'bg-white ring-1 ring-gray-200'
                }`}>
                  {/* Interviewer Header - Video Call Style */}
                  <div className={`p-4 border-b backdrop-blur-sm ${
                    theme === 'dark' 
                      ? 'border-gray-700 bg-gradient-to-r from-gray-800 to-gray-750' 
                      : 'border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50'
                  }`}>
                    <div className="flex items-center space-x-3">
                      {/* AI Interviewer Avatar */}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        theme === 'dark' 
                          ? 'bg-gradient-to-br from-blue-500 to-purple-600 ring-2 ring-blue-400/30' 
                          : 'bg-gradient-to-br from-blue-500 to-purple-600 ring-2 ring-blue-400/50'
                      }`}>
                        <span className="text-white font-bold text-sm">AI</span>
                      </div>
                      <div>
                        <h3 className={`font-semibold text-sm ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                          System Design Interviewer
                        </h3>
                        <div className="flex items-center space-x-1">
                          <div className={`w-2 h-2 rounded-full ${
                            isLoading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'
                          }`}></div>
                          <span className={`text-xs ${
                            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            {isLoading ? 'Thinking...' : 'Online'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Chat Interface */}
                  <div className="flex-1 min-h-0">
                    <ChatInterface
                      messages={messages}
                      onSendMessage={handleSendMessage}
                      onRequestAssessment={handleRequestAssessment}
                      isLoading={isLoading}
                      showAssessmentButton={true}
                      onVoiceTranscriptStart={handleVoiceTranscriptStart}
                      onVoiceTranscriptUpdate={handleVoiceTranscriptUpdate}
                      onVoiceTranscriptComplete={handleVoiceTranscriptComplete}
                      sessionId={sessionId}
                    />
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}