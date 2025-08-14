import React from 'react'
import { render, screen, fireEvent } from './test-utils'
import { AssessmentButton } from '../components/AssessmentButton'

describe('AssessmentButton', () => {
    const mockOnRequestAssessment = jest.fn()

    beforeEach(() => {
        jest.clearAllMocks()
    })

    it('renders assessment button with correct text', () => {
        render(<AssessmentButton onRequestAssessment={mockOnRequestAssessment} />)

        expect(screen.getByText('🎯 Get Assessment')).toBeInTheDocument()
        expect(screen.getByTestId('assessment-button')).toBeInTheDocument()
    })

    it('calls onRequestAssessment when clicked', () => {
        render(<AssessmentButton onRequestAssessment={mockOnRequestAssessment} />)

        const button = screen.getByTestId('assessment-button')
        fireEvent.click(button)

        expect(mockOnRequestAssessment).toHaveBeenCalledTimes(1)
    })

    it('shows loading state when isLoading is true', () => {
        render(
            <AssessmentButton
                onRequestAssessment={mockOnRequestAssessment}
                isLoading={true}
            />
        )

        expect(screen.getByText('Getting Assessment...')).toBeInTheDocument()
        expect(screen.getByText('Getting Assessment...')).toBeDisabled()
    })

    it('is disabled when disabled prop is true', () => {
        render(
            <AssessmentButton
                onRequestAssessment={mockOnRequestAssessment}
                disabled={true}
            />
        )

        const button = screen.getByTestId('assessment-button')
        expect(button).toBeDisabled()
    })

    it('is disabled when loading', () => {
        render(
            <AssessmentButton
                onRequestAssessment={mockOnRequestAssessment}
                isLoading={true}
            />
        )

        const button = screen.getByTestId('assessment-button')
        expect(button).toBeDisabled()
    })

    it('applies custom className', () => {
        render(
            <AssessmentButton
                onRequestAssessment={mockOnRequestAssessment}
                className="custom-class"
            />
        )

        const button = screen.getByTestId('assessment-button')
        expect(button).toHaveClass('custom-class')
    })
})
