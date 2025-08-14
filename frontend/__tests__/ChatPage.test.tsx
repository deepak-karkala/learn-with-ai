import React from 'react'
import { render, screen, fireEvent, waitFor } from './test-utils'
import '@testing-library/jest-dom'
import ChatPage from '../app/chat/page'

// Mock the ChatInterface component
jest.mock('../components/ChatInterface', () => ({
    ChatInterface: ({ messages, onSendMessage, onRequestAssessment, isLoading }: any) => (
        <div data-testid="chat-interface">
            <div>Messages: {messages.length}</div>
            <button onClick={() => onSendMessage('test message')}>
                Send Message
            </button>
            <button onClick={onRequestAssessment}>
                Request Assessment
            </button>
            {isLoading && <div>Loading...</div>}
        </div>
    )
}))

// Mock the WhiteboardCanvas component
jest.mock('../components/WhiteboardCanvas', () => ({
    WhiteboardCanvas: ({ onSave, onAnalyze, isAnalyzing }: any) => (
        <div data-testid="whiteboard-canvas">
            <button onClick={() => onSave('mock-png-data')}>
                Save Whiteboard
            </button>
            <button onClick={() => onAnalyze('mock-png-data')}>
                Analyze Whiteboard
            </button>
            {isAnalyzing && <div>Analyzing...</div>}
        </div>
    )
}))

// Mock the ProgressDashboard component
jest.mock('../components/ProgressDashboard', () => ({
    ProgressDashboard: ({ data, userId, onExportReport, onSetGoal, onUpdateGoal }: any) => (
        <div data-testid="progress-dashboard">
            <div>User: {userId}</div>
            <button onClick={onExportReport}>Export Report</button>
            <button onClick={() => onSetGoal({ description: 'Test Goal' })}>Set Goal</button>
            <button onClick={() => onUpdateGoal('goal-1', 100, 'completed')}>Update Goal</button>
            {data && <div>Timeline Points: {data.timeline?.points?.length || 0}</div>}
        </div>
    )
}))

// Mock the Sidebar component
jest.mock('../components/Sidebar', () => ({
    Sidebar: ({ sessions, onNewSession, onSelectSession }: any) => (
        <div data-testid="sidebar">
            <button onClick={onNewSession}>New Session</button>
            <div>Sessions: {sessions.length}</div>
            <button onClick={() => onSelectSession('session-1')}>Select Session</button>
        </div>
    )
}))

// Mock fetch globally
global.fetch = jest.fn()

describe('ChatPage', () => {
    beforeEach(() => {
        jest.clearAllMocks()
        ;(fetch as jest.Mock).mockClear()
    })

    it('renders the main chat and whiteboard panels', () => {
        render(<ChatPage />)
        // Should render chat interface and whiteboard components
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument()
        expect(screen.getByTestId('whiteboard-canvas')).toBeInTheDocument()
    })

    it('renders the sidebar with session management', () => {
        render(<ChatPage />)
        
        expect(screen.getByTestId('sidebar')).toBeInTheDocument()
        expect(screen.getByText('New Session')).toBeInTheDocument()
        expect(screen.getByText('Sessions: 4')).toBeInTheDocument() // Mock sessions
    })

    it('shows chat interface and whiteboard canvas side by side', () => {
        render(<ChatPage />)
        
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument()
        expect(screen.getByTestId('whiteboard-canvas')).toBeInTheDocument()
        expect(screen.getByText('Messages: 0')).toBeInTheDocument()
    })

    it('handles chat and whiteboard functionality in main view', async () => {
        render(<ChatPage />)
        
        // Should show both chat and whiteboard in the main view
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument()
        expect(screen.getByTestId('whiteboard-canvas')).toBeInTheDocument()
        expect(screen.getByText('Messages: 0')).toBeInTheDocument()
    })

    it('displays sidebar navigation correctly', async () => {
        render(<ChatPage />)
        
        expect(screen.getByTestId('sidebar')).toBeInTheDocument()
        expect(screen.getByText('New Session')).toBeInTheDocument()
        expect(screen.getByText('Sessions: 4')).toBeInTheDocument()
    })

    it('handles chat message sending', async () => {
        // Mock successful chat response
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                message: 'AI response',
                session_id: 'test-session-123'
            })
        })

        render(<ChatPage />)
        
        const sendButton = screen.getByText('Send Message')
        fireEvent.click(sendButton)
        
        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith('/api/chat', expect.objectContaining({
                method: 'POST',
                body: expect.stringContaining('test message')
            }))
        })
    })

    it('handles assessment request', async () => {
        // First mock chat response to get messages
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                message: 'AI response',
                session_id: 'test-session-123'
            })
        })
        
        // Then mock assessment response
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                overall_score: 4.2,
                dimension_scores: {}
            })
        })

        render(<ChatPage />)
        
        // First send a message to make assessment button appear
        const sendButton = screen.getByText('Send Message')
        fireEvent.click(sendButton)
        
        await waitFor(() => {
            expect(screen.getByText('Messages: 2')).toBeInTheDocument()
        })
        
        // Now find and click assessment button
        const assessmentButton = screen.getByText('Request Assessment')
        fireEvent.click(assessmentButton)
        
        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith('/api/assessment/evaluate', expect.objectContaining({
                method: 'POST'
            }))
        })
    })

    it('handles whiteboard PNG upload', async () => {
        // Mock successful upload response
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                artifact_id: 'artifact-123'
            })
        })

        render(<ChatPage />)
        
        // Whiteboard should be visible in main view
        const saveButton = screen.getByText('Save Whiteboard')
        fireEvent.click(saveButton)

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith('/api/whiteboard/upload', expect.objectContaining({
                method: 'POST',
                body: expect.stringContaining('mock-png-data')
            }))
        })
    })

    it('handles whiteboard analysis', async () => {
        // Mock upload and analysis responses
        ;(fetch as jest.Mock)
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({ artifact_id: 'artifact-123' })
            })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    components_identified: ['Load Balancer', 'Database'],
                    architectural_feedback: 'Good design',
                    suggestions: ['Add caching'],
                    confidence_score: 0.85
                })
            })

        render(<ChatPage />)
        
        // Whiteboard should be visible in main view
        const analyzeButton = screen.getByText('Analyze Whiteboard')
        fireEvent.click(analyzeButton)

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith('/api/whiteboard/upload', expect.any(Object))
            expect(fetch).toHaveBeenCalledWith('/api/whiteboard/analyze', expect.any(Object))
        })
    })

    it('persists session ID in localStorage', () => {
        const mockSetItem = jest.fn()
        const mockGetItem = jest.fn().mockReturnValue('existing-session-id')
        
        Object.defineProperty(window, 'localStorage', {
            value: {
                getItem: mockGetItem,
                setItem: mockSetItem
            },
            writable: true
        })

        render(<ChatPage />)
        
        expect(mockGetItem).toHaveBeenCalledWith('sessionId:john@example.com')
    })

    it('handles session management through sidebar', async () => {
        render(<ChatPage />)
        
        // Should show sidebar with sessions
        expect(screen.getByTestId('sidebar')).toBeInTheDocument()
        expect(screen.getByText('Sessions: 4')).toBeInTheDocument()
        
        // Should allow session selection
        const selectSessionButton = screen.getByText('Select Session')
        fireEvent.click(selectSessionButton)
        
        // Should allow new session creation
        const newSessionButton = screen.getByText('New Session')
        expect(newSessionButton).toBeInTheDocument()
    })

    it('has consistent layout structure', async () => {
        render(<ChatPage />)
        
        // Should have sidebar, chat, and whiteboard in consistent layout
        expect(screen.getByTestId('sidebar')).toBeInTheDocument()
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument()
        expect(screen.getByTestId('whiteboard-canvas')).toBeInTheDocument()
        
        // Should show initial empty state
        expect(screen.getByText('Messages: 0')).toBeInTheDocument()
    })
})

describe('ChatPage Error Handling', () => {
    beforeEach(() => {
        jest.clearAllMocks()
        ;(fetch as jest.Mock).mockClear()
    })

    it('handles chat API errors gracefully', async () => {
        const mockAlert = jest.spyOn(window, 'alert').mockImplementation(() => {})
        
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            status: 500
        })

        render(<ChatPage />)
        
        const sendButton = screen.getByText('Send Message')
        fireEvent.click(sendButton)
        
        await waitFor(() => {
            expect(screen.getByText('Messages: 2')).toBeInTheDocument() // User message + error message
        })
        
        mockAlert.mockRestore()
    })

    it('handles whiteboard upload errors', async () => {
        const mockAlert = jest.spyOn(window, 'alert').mockImplementation(() => {})
        
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            status: 413 // Payload too large
        })

        render(<ChatPage />)
        
        // Whiteboard should be visible in main view
        const saveButton = screen.getByText('Save Whiteboard')
        fireEvent.click(saveButton)

        await waitFor(() => {
            expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining('Upload failed'))
        })
        
        mockAlert.mockRestore()
    })

    it('handles assessment request errors', async () => {
        const mockAlert = jest.spyOn(window, 'alert').mockImplementation(() => {})
        
        // First mock chat response to get messages
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                message: 'AI response',
                session_id: 'test-session-123'
            })
        })
        
        // Then mock assessment error response
        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            status: 400
        })

        render(<ChatPage />)
        
        // First send a message to make assessment button appear
        const sendButton = screen.getByText('Send Message')
        fireEvent.click(sendButton)
        
        await waitFor(() => {
            expect(screen.getByText('Messages: 2')).toBeInTheDocument()
        })
        
        const assessmentButton = screen.getByText('Request Assessment')
        fireEvent.click(assessmentButton)
        
        await waitFor(() => {
            expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining('Assessment failed'))
        })
        
        mockAlert.mockRestore()
    })
})

describe('ChatPage Session Management', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    it('loads existing session from localStorage', () => {
        const mockGetItem = jest.fn().mockReturnValue('existing-session-123')
        const mockSetItem = jest.fn()
        
        Object.defineProperty(window, 'localStorage', {
            value: {
                getItem: mockGetItem,
                setItem: mockSetItem
            },
            writable: true
        })

        render(<ChatPage />)
        
        expect(mockGetItem).toHaveBeenCalledWith('sessionId:john@example.com')
    })

    it('saves new session ID from API response', async () => {
        const mockSetItem = jest.fn()
        const mockGetItem = jest.fn().mockReturnValue(null)
        
        Object.defineProperty(window, 'localStorage', {
            value: {
                getItem: mockGetItem,
                setItem: mockSetItem
            },
            writable: true
        })

        ;(fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                message: 'AI response',
                session_id: 'new-session-456'
            })
        })

        render(<ChatPage />)
        
        const sendButton = screen.getByText('Send Message')
        fireEvent.click(sendButton)
        
        await waitFor(() => {
            // The message count should include user message and AI response
            expect(screen.getByText('Messages: 2')).toBeInTheDocument()
        })

        // Check that setItem was called at some point
        await waitFor(() => {
            expect(mockSetItem).toHaveBeenCalled()
        })
    })
})