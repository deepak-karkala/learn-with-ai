import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatInterface, Message } from '@/components/ChatInterface'

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
    Send: () => <span data-testid="send-icon">Send</span>,
    Bot: () => <span data-testid="bot-icon">Bot</span>,
    User: () => <span data-testid="user-icon">User</span>,
    AlertCircle: () => <span data-testid="alert-icon">Alert</span>,
}))

describe('ChatInterface', () => {
    const mockOnSendMessage = jest.fn().mockResolvedValue(undefined)
    const mockMessages: Message[] = [
        {
            id: '1',
            content: 'Hello, how are you?',
            role: 'user',
            timestamp: new Date('2024-01-01T10:00:00Z')
        },
        {
            id: '2',
            content: 'I\'m doing well, thank you! How can I help you with system design today?',
            role: 'assistant',
            timestamp: new Date('2024-01-01T10:01:00Z')
        }
    ]

    beforeEach(() => {
        mockOnSendMessage.mockClear()
    })

    it('renders correctly with no messages', () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} />)

        expect(screen.getByText('Welcome to System Design Learning!')).toBeInTheDocument()
        expect(screen.getByPlaceholderText('Ask about system design concepts, architecture patterns, or start drawing...')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
    })

    it('displays messages correctly', () => {
        render(<ChatInterface messages={mockMessages} onSendMessage={mockOnSendMessage} />)

        expect(screen.getByText('Hello, how are you?')).toBeInTheDocument()
        expect(screen.getByText('I\'m doing well, thank you! How can I help you with system design today?')).toBeInTheDocument()
    })

    it('sends message when form submitted', async () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} />)

        const input = screen.getByPlaceholderText('Ask about system design concepts, architecture patterns, or start drawing...')
        const button = screen.getByRole('button', { name: /send/i })

        fireEvent.change(input, { target: { value: 'Hello' } })
        fireEvent.click(button)

        await waitFor(() => {
            expect(mockOnSendMessage).toHaveBeenCalledWith('Hello')
        })
    })

    it('sends message when Enter key pressed', async () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} />)

        const input = screen.getByPlaceholderText('Ask about system design concepts, architecture patterns, or start drawing...')
        const form = input.closest('form')

        fireEvent.change(input, { target: { value: 'Hello' } })
        fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', keyCode: 13 })

        await waitFor(() => {
            expect(mockOnSendMessage).toHaveBeenCalledWith('Hello')
        })
    })

    it('does not send message when Shift+Enter pressed', () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} />)

        const input = screen.getByPlaceholderText('Ask about system design concepts, architecture patterns, or start drawing...')

        fireEvent.change(input, { target: { value: 'Hello\nWorld' } })
        fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', shiftKey: true })

        expect(mockOnSendMessage).not.toHaveBeenCalled()
    })

    it('disables input and button when loading', () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} isLoading={true} />)

        const input = screen.getByPlaceholderText('Ask about system design concepts, architecture patterns, or start drawing...')
        const button = screen.getByRole('button', { name: /send/i })

        expect(input).toBeDisabled()
        expect(button).toBeDisabled()
    })

    it('displays error message when error is provided', () => {
        const errorMessage = 'Something went wrong'
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} error={errorMessage} />)

        expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    it('displays typing indicator when isTyping is true', () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} isTyping={true} />)

        expect(screen.getByText('AI is typing...')).toBeInTheDocument()
    })

    it('clears input after sending message', async () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} />)

        const input = screen.getByPlaceholderText('Ask about system design concepts, architecture patterns, or start drawing...')
        const button = screen.getByRole('button', { name: /send/i })

        fireEvent.change(input, { target: { value: 'Hello' } })
        fireEvent.click(button)

        await waitFor(() => {
            expect(input).toHaveValue('')
        })
    })

    it('does not send empty messages', () => {
        render(<ChatInterface messages={[]} onSendMessage={mockOnSendMessage} />)

        const button = screen.getByRole('button', { name: /send/i })

        expect(button).toBeDisabled()

        fireEvent.click(button)
        expect(mockOnSendMessage).not.toHaveBeenCalled()
    })

    it('displays message count correctly', () => {
        render(<ChatInterface messages={mockMessages} onSendMessage={mockOnSendMessage} />)

        expect(screen.getByText('2 messages')).toBeInTheDocument()
    })

    it('displays assessment scores when available', () => {
        const messagesWithAssessment: Message[] = [
            {
                id: '1',
                content: 'Here is your assessment',
                role: 'assistant',
                timestamp: new Date('2024-01-01T10:00:00Z'),
                metadata: {
                    assessment: {
                        requirements_analysis: 4,
                        system_architecture: 5,
                        technical_deep_dive: 3,
                        scale_performance: 4,
                        reliability_fault_tolerance: 4,
                        communication_thought_process: 5
                    }
                }
            }
        ]

        render(<ChatInterface messages={messagesWithAssessment} onSendMessage={mockOnSendMessage} />)

        expect(screen.getByText('Assessment Scores:')).toBeInTheDocument()
        expect(screen.getByText('requirements analysis:')).toBeInTheDocument()
        expect(screen.getByText('system architecture:')).toBeInTheDocument()
        expect(screen.getByText('technical deep dive:')).toBeInTheDocument()
        expect(screen.getByText('3/5')).toBeInTheDocument()
    })
})
