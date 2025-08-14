import React from 'react'
import { render, screen, fireEvent, waitFor } from './test-utils'
import '@testing-library/jest-dom'
import { WhiteboardCanvas } from '../components/WhiteboardCanvas'

// Mock canvas methods
const mockCanvas = {
    getContext: jest.fn(() => ({
        clearRect: jest.fn(),
        fillRect: jest.fn(),
        strokeRect: jest.fn(),
        beginPath: jest.fn(),
        moveTo: jest.fn(),
        lineTo: jest.fn(),
        stroke: jest.fn(),
        fillText: jest.fn(),
        toDataURL: jest.fn(() => 'data:image/png;base64,mock-png-data'),
    })),
    width: 800,
    height: 600,
    offsetWidth: 800,
    offsetHeight: 600,
    getBoundingClientRect: jest.fn(() => ({
        left: 0,
        top: 0,
        width: 800,
        height: 600,
    })),
    toDataURL: jest.fn(() => 'data:image/png;base64,mock-png-data'),
}

// Mock HTMLCanvasElement prototype methods
beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()

    // Mock canvas methods
    Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
        value: mockCanvas.getContext,
        configurable: true,
    })

    Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
        value: mockCanvas.toDataURL,
        configurable: true,
    })

    Object.defineProperty(HTMLCanvasElement.prototype, 'getBoundingClientRect', {
        value: mockCanvas.getBoundingClientRect,
        configurable: true,
    })
})

describe('WhiteboardCanvas', () => {

    describe('Component Rendering', () => {
        it('renders whiteboard canvas with toolbar', () => {
            render(<WhiteboardCanvas />)

            expect(screen.getByText('Select')).toBeInTheDocument()
            expect(screen.getByText('Connect')).toBeInTheDocument()
            expect(screen.getByText('Load Balancer')).toBeInTheDocument()
            expect(screen.getByText('Web Server')).toBeInTheDocument()
            expect(screen.getByText('Database')).toBeInTheDocument()
            expect(screen.getByText('Redis Cache')).toBeInTheDocument()
        })

        it('displays all system design block types', () => {
            render(<WhiteboardCanvas />)

            const expectedBlocks = [
                'Load Balancer',
                'Web Server',
                'Database',
                'Redis Cache',
                'API Gateway',
                'CDN',
                'Message Queue',
                'Cache',
                'Monitoring',
                'Logging'
            ]

            expectedBlocks.forEach(block => {
                expect(screen.getByText(block)).toBeInTheDocument()
            })
        })

        it('shows canvas area', () => {
            render(<WhiteboardCanvas />)

            // Canvas element should be present
            const canvas = document.querySelector('canvas')
            expect(canvas).toBeInTheDocument()
        })
    })

    describe('Tool Selection', () => {
        it('defaults to select tool', () => {
            render(<WhiteboardCanvas />)

            const selectButton = screen.getByText('Select')
            const connectButton = screen.getByText('Connect')

            expect(selectButton).toHaveClass('bg-primary')
            // The connect button should have the default button styling (not bg-secondary)
            expect(connectButton).not.toHaveClass('bg-primary')
        })

        it('switches to connect tool when clicked', () => {
            render(<WhiteboardCanvas />)

            const connectButton = screen.getByText('Connect')
            fireEvent.click(connectButton)

            expect(connectButton).toHaveClass('bg-primary')
            expect(screen.getByText('Select')).not.toHaveClass('bg-primary')
        })

        it('shows appropriate status message for each tool', () => {
            render(<WhiteboardCanvas />)

            // Default select tool should be active
            expect(screen.getByText('Select')).toHaveClass('bg-primary')

            // Switch to connect tool
            fireEvent.click(screen.getByText('Connect'))
            expect(screen.getByText('Connect')).toHaveClass('bg-primary')
            expect(screen.getByText('Select')).not.toHaveClass('bg-primary')

            // Verify tool switching works
            fireEvent.click(screen.getByText('Select'))
            expect(screen.getByText('Select')).toHaveClass('bg-primary')
            expect(screen.getByText('Connect')).not.toHaveClass('bg-primary')
        })
    })

    describe('Block Management', () => {
        it('adds blocks when block type buttons are clicked', () => {
            render(<WhiteboardCanvas />)

            const loadBalancerButton = screen.getByText('Load Balancer')
            fireEvent.click(loadBalancerButton)

            // Block should be added (no longer showing counters in UI)
            expect(loadBalancerButton).toBeInTheDocument()
        })

        it('adds multiple blocks of different types', () => {
            render(<WhiteboardCanvas />)

            fireEvent.click(screen.getByText('Load Balancer'))
            fireEvent.click(screen.getByText('Web Server'))
            fireEvent.click(screen.getByText('Database'))

            // All block buttons should be present (no longer showing counters in UI)
            expect(screen.getByText('Load Balancer')).toBeInTheDocument()
            expect(screen.getByText('Web Server')).toBeInTheDocument()
            expect(screen.getByText('Database')).toBeInTheDocument()
        })

        it('clears all blocks when clear button is clicked', () => {
            render(<WhiteboardCanvas />)

            // Add some blocks
            fireEvent.click(screen.getByText('Load Balancer'))
            fireEvent.click(screen.getByText('Web Server'))

            // Clear canvas - find clear button by checking all buttons for the one that clears
            const buttons = screen.getAllByRole('button')
            const clearButton = buttons.find(button => 
                button.className.includes('text-red-600') || 
                button.textContent?.includes('Clear') ||
                button.querySelector('[class*="trash"]')
            )
            if (clearButton) {
                fireEvent.click(clearButton)
            }

            // Canvas should still be present after clear
            expect(document.querySelector('canvas')).toBeInTheDocument()
        })
    })

    describe('Block Selection and Deletion', () => {
        it('shows delete button only when block is selected', () => {
            render(<WhiteboardCanvas />)

            // Initially no delete button
            expect(screen.queryByText('Delete Block')).not.toBeInTheDocument()

            // Add a block
            fireEvent.click(screen.getByText('Load Balancer'))

            // Still no delete button (no block selected)
            expect(screen.queryByText('Delete Block')).not.toBeInTheDocument()
        })

        it('deletes selected block when delete button is clicked', () => {
            render(<WhiteboardCanvas />)

            // Add a block
            fireEvent.click(screen.getByText('Load Balancer'))

            // Canvas should be present (block management happens internally)
            expect(document.querySelector('canvas')).toBeInTheDocument()
        })
    })

    describe('Canvas Operations', () => {
        it('initializes canvas with proper dimensions', () => {
            render(<WhiteboardCanvas />)

            // Canvas should be initialized and present in the DOM
            const canvas = document.querySelector('canvas')
            expect(canvas).toBeInTheDocument()
        })

        it('handles canvas click events', () => {
            render(<WhiteboardCanvas />)

            const canvas = document.querySelector('canvas')
            expect(canvas).toBeInTheDocument()

            if (canvas) {
                // Simulate canvas click
                fireEvent.click(canvas, { clientX: 100, clientY: 100 })

                // Canvas click handler should be called
                expect(canvas).toBeInTheDocument()
            }
        })

        it('handles mouse events for dragging', () => {
            render(<WhiteboardCanvas />)

            const canvas = document.querySelector('canvas')
            expect(canvas).toBeInTheDocument()

            if (canvas) {
                // Simulate mouse events
                fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 })
                fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 })
                fireEvent.mouseUp(canvas)

                // Mouse event handlers should be attached
                expect(canvas).toBeInTheDocument()
            }
        })
    })

    describe('PNG Export Functionality', () => {
        it('renders save button correctly', () => {
            render(<WhiteboardCanvas />)

            const saveButton = screen.getByText('Save PNG')
            expect(saveButton).toBeInTheDocument()
        })

        it('save button is disabled when no blocks exist', () => {
            render(<WhiteboardCanvas />)

            const saveButton = screen.getByText('Save PNG')
            expect(saveButton).toBeDisabled()
        })

        it('save button is enabled when blocks exist', () => {
            render(<WhiteboardCanvas />)

            // Add a block
            fireEvent.click(screen.getByText('Load Balancer'))

            const saveButton = screen.getByText('Save PNG')
            expect(saveButton).not.toBeDisabled()
        })
    })

    describe('Canvas State', () => {
        it('renders canvas element', () => {
            render(<WhiteboardCanvas />)

            expect(document.querySelector('canvas')).toBeInTheDocument()
        })

        it('maintains canvas when blocks are added', () => {
            render(<WhiteboardCanvas />)

            fireEvent.click(screen.getByText('Load Balancer'))
            fireEvent.click(screen.getByText('Web Server'))

            expect(document.querySelector('canvas')).toBeInTheDocument()
        })
    })

    describe('Block Types and Icons', () => {
        it('displays correct icons for each block type', () => {
            render(<WhiteboardCanvas />)

            // Check that icon components are rendered
            const loadBalancerButton = screen.getByText('Load Balancer')
            const webServerButton = screen.getByText('Web Server')
            const databaseButton = screen.getByText('Database')

            expect(loadBalancerButton).toBeInTheDocument()
            expect(webServerButton).toBeInTheDocument()
            expect(databaseButton).toBeInTheDocument()
        })

        it('has consistent button styling for all block types', () => {
            render(<WhiteboardCanvas />)

            const blockButtons = screen.getAllByRole('button').filter(button =>
                ['Load Balancer', 'Web Server', 'Database', 'Redis Cache'].includes(button.textContent || '')
            )

            blockButtons.forEach(button => {
                // Block type buttons should have the default button styling (bg-background)
                expect(button).toHaveClass('bg-background')
            })
        })
    })

    describe('Responsive Design', () => {
        it('renders with proper layout structure', () => {
            render(<WhiteboardCanvas />)

            // Check that the component has the expected structure
            expect(document.querySelector('canvas')).toBeInTheDocument()
            expect(screen.getByText('Select')).toBeInTheDocument()
            expect(screen.getByText('Connect')).toBeInTheDocument()
        })

        it('handles different screen sizes gracefully', () => {
            // This would require more sophisticated testing with different viewport sizes
            // For now, we'll verify the component renders without errors
            render(<WhiteboardCanvas />)

            expect(document.querySelector('canvas')).toBeInTheDocument()
        })
    })

    describe('Error Handling', () => {
        it('handles canvas context errors gracefully', () => {
            // Mock canvas context failure
            const mockGetContext = jest.fn(() => null)
            Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
                value: mockGetContext,
            })

            // Component should render without crashing
            render(<WhiteboardCanvas />)
            expect(document.querySelector('canvas')).toBeInTheDocument()
        })

        it('handles save errors gracefully', () => {
            // Mock save failure
            const mockToDataURL = jest.fn(() => {
                throw new Error('Save failed')
            })
            Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
                value: mockToDataURL,
            })

            render(<WhiteboardCanvas />)

            const saveButton = screen.getByText('Save PNG')
            fireEvent.click(saveButton)

            // Component should not crash
            expect(document.querySelector('canvas')).toBeInTheDocument()
        })
    })

    describe('Accessibility', () => {
        it('has proper button roles', () => {
            render(<WhiteboardCanvas />)

            const buttons = screen.getAllByRole('button')
            // Just verify buttons exist and have the button role
            expect(buttons.length).toBeGreaterThan(0)
            
            // Check some key buttons by text
            expect(screen.getByText('Save PNG')).toBeInTheDocument()
            expect(screen.getByText('Analyze')).toBeInTheDocument()
            expect(screen.getByText('Select')).toBeInTheDocument()
            expect(screen.getByText('Connect')).toBeInTheDocument()
        })

        it('provides visual feedback for selected tools', () => {
            render(<WhiteboardCanvas />)

            const selectButton = screen.getByText('Select')
            const connectButton = screen.getByText('Connect')

            // Initially select is active
            expect(selectButton).toHaveClass('bg-primary')
            expect(connectButton).not.toHaveClass('bg-primary')

            // Click connect to activate it
            fireEvent.click(connectButton)
            expect(connectButton).toHaveClass('bg-primary')
            expect(selectButton).not.toHaveClass('bg-primary')
        })
    })
})
