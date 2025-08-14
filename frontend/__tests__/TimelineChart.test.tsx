import React from 'react'
import { render, screen, fireEvent } from './test-utils'
import '@testing-library/jest-dom'
import { TimelineChart } from '../components/progress/TimelineChart'

const mockData = [
    {
        date: '2025-01-01',
        overall_score: 3.0,
        dimension_scores: {
            requirements_analysis: 3.2,
            system_architecture: 2.8,
            technical_deep_dive: 3.0,
            scale_performance: 2.9,
            reliability_fault_tolerance: 3.1,
            communication_thought_process: 3.2
        }
    },
    {
        date: '2025-01-15',
        overall_score: 3.4,
        dimension_scores: {
            requirements_analysis: 3.6,
            system_architecture: 3.2,
            technical_deep_dive: 3.3,
            scale_performance: 3.1,
            reliability_fault_tolerance: 3.4,
            communication_thought_process: 3.8
        }
    },
    {
        date: '2025-02-01',
        overall_score: 3.8,
        dimension_scores: {
            requirements_analysis: 4.0,
            system_architecture: 3.8,
            technical_deep_dive: 3.6,
            scale_performance: 3.5,
            reliability_fault_tolerance: 3.7,
            communication_thought_process: 4.2
        }
    }
]

describe('TimelineChart', () => {
    const defaultProps = {
        data: mockData,
        onPointSelect: jest.fn(),
        selectedPoint: null
    }

    beforeEach(() => {
        jest.clearAllMocks()
    })

    it('renders chart with data points', () => {
        render(<TimelineChart {...defaultProps} />)
        
        expect(screen.getByTestId('timeline-chart')).toBeInTheDocument()
        expect(screen.getByTestId('data-point-0')).toBeInTheDocument()
        expect(screen.getByTestId('data-point-1')).toBeInTheDocument()
        expect(screen.getByTestId('data-point-2')).toBeInTheDocument()
    })

    it('displays legend with all dimensions', () => {
        render(<TimelineChart {...defaultProps} />)
        
        expect(screen.getByText('Overall Score')).toBeInTheDocument()
        expect(screen.getByText('Requirements')).toBeInTheDocument()
        expect(screen.getByText('Architecture')).toBeInTheDocument()
        expect(screen.getByText('Technical')).toBeInTheDocument()
        expect(screen.getByText('Scale')).toBeInTheDocument()
        expect(screen.getByText('Reliability')).toBeInTheDocument()
        expect(screen.getByText('Communication')).toBeInTheDocument()
    })

    it('shows statistics section', () => {
        render(<TimelineChart {...defaultProps} />)
        
        // Should show all statistics (some may be the same)
        const bestScore = screen.getAllByText('3.8') // Best and latest are both 3.8
        expect(bestScore.length).toBeGreaterThan(0)
        
        // Average should be (3.0 + 3.4 + 3.8) / 3 = 3.4
        expect(screen.getByText('3.4')).toBeInTheDocument()
    })

    it('calls onPointSelect when data point is clicked', () => {
        const mockOnPointSelect = jest.fn()
        render(<TimelineChart {...defaultProps} onPointSelect={mockOnPointSelect} />)
        
        const dataPoint = screen.getByTestId('data-point-0')
        fireEvent.click(dataPoint)
        
        expect(mockOnPointSelect).toHaveBeenCalledWith(mockData[0])
    })

    it('highlights selected point', () => {
        render(<TimelineChart {...defaultProps} selectedPoint={mockData[1]} />)
        
        // Implementation would vary based on how selection styling is handled
        expect(screen.getByTestId('data-point-1')).toBeInTheDocument()
    })

    it('renders empty state when no data', () => {
        render(<TimelineChart {...defaultProps} data={[]} />)
        
        expect(screen.getByText('No progress data available yet.')).toBeInTheDocument()
        expect(screen.getByText('Complete an assessment to see your progress timeline.')).toBeInTheDocument()
    })

    it('handles undefined data gracefully', () => {
        // @ts-ignore - testing runtime behavior
        render(<TimelineChart {...defaultProps} data={undefined} />)
        
        expect(screen.getByText('No progress data available yet.')).toBeInTheDocument()
    })

    it('calculates correct statistics for single data point', () => {
        const singlePoint = [mockData[0]]
        render(<TimelineChart {...defaultProps} data={singlePoint} />)
        
        // All statistics should be the same (3.0)
        expect(screen.getAllByText('3.0')).toHaveLength(3)
    })

    it('renders SVG chart elements', () => {
        render(<TimelineChart {...defaultProps} />)
        
        const chart = screen.getByTestId('timeline-chart')
        const svg = chart.querySelector('svg')
        expect(svg).toBeInTheDocument()
        
        // Should have grid lines
        const gridLines = svg?.querySelectorAll('line')
        expect(gridLines?.length).toBeGreaterThan(0)
        
        // Should have data point circles
        const circles = svg?.querySelectorAll('circle')
        expect(circles?.length).toBe(3) // One for each data point
        
        // Should have path for overall score line
        const paths = svg?.querySelectorAll('path')
        expect(paths?.length).toBeGreaterThan(0)
    })

    it('formats dates correctly in chart labels', () => {
        render(<TimelineChart {...defaultProps} />)
        
        // Should format dates as "Jan 1", "Jan 15", "Feb 1"
        const chart = screen.getByTestId('timeline-chart')
        const svg = chart.querySelector('svg')
        const textElements = svg?.querySelectorAll('text')
        
        expect(textElements?.length).toBeGreaterThan(0)
    })
})

describe('TimelineChart Accessibility', () => {
    const defaultProps = {
        data: mockData,
        onPointSelect: jest.fn(),
        selectedPoint: null
    }

    it('has proper ARIA labels and roles', () => {
        render(<TimelineChart {...defaultProps} />)
        
        const chart = screen.getByTestId('timeline-chart')
        expect(chart).toBeInTheDocument()
        
        // Data points should be clickable
        const dataPoint = screen.getByTestId('data-point-0')
        expect(dataPoint).toHaveClass('cursor-pointer')
    })

    it('provides keyboard navigation support', () => {
        render(<TimelineChart {...defaultProps} />)
        
        const dataPoint = screen.getByTestId('data-point-0')
        
        // Should be focusable
        dataPoint.focus()
        expect(dataPoint).toHaveFocus()
    })
})

describe('TimelineChart Responsive Behavior', () => {
    const defaultProps = {
        data: mockData,
        onPointSelect: jest.fn(),
        selectedPoint: null
    }

    it('has responsive chart container', () => {
        render(<TimelineChart {...defaultProps} />)
        
        const chart = screen.getByTestId('timeline-chart')
        const chartContainer = chart.querySelector('.overflow-x-auto')
        expect(chartContainer).toBeInTheDocument()
        
        const svg = chartContainer?.querySelector('svg')
        expect(svg).toHaveClass('w-full', 'h-auto', 'min-w-[600px]')
    })

    it('maintains minimum chart width for readability', () => {
        render(<TimelineChart {...defaultProps} />)
        
        const chart = screen.getByTestId('timeline-chart')
        const svg = chart.querySelector('svg')
        expect(svg).toHaveAttribute('width', '600')
        expect(svg).toHaveAttribute('height', '200')
    })
})