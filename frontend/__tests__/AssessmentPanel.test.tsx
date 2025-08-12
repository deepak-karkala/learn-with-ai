import React from 'react'
import { render, screen } from '@testing-library/react'
import { AssessmentPanel } from '../components/AssessmentPanel'

const mockAssessment = {
    assessment_id: 'test-123',
    user_id: 'test-user',
    overall_score: 4.2,
    confidence_score: 4.1,
    dimension_scores: {
        requirements_analysis: {
            score: 4.0,
            feedback: 'Good understanding of requirements',
            strengths: ['Clear problem identification', 'Good scope definition'],
            areas_for_improvement: ['Consider edge cases', 'Think about scalability'],
            confidence: 4.2
        },
        system_architecture: {
            score: 4.5,
            feedback: 'Excellent architectural design',
            strengths: ['Clean separation of concerns', 'Good component design'],
            areas_for_improvement: ['Consider failure modes'],
            confidence: 4.3
        },
        technical_deep_dive: {
            score: 3.8,
            feedback: 'Solid technical knowledge',
            strengths: ['Good understanding of technologies'],
            areas_for_improvement: ['Dive deeper into trade-offs'],
            confidence: 3.9
        },
        scale_performance: {
            score: 4.1,
            feedback: 'Good performance considerations',
            strengths: ['Load balancing awareness', 'Caching strategies'],
            areas_for_improvement: ['Consider bottlenecks'],
            confidence: 4.0
        },
        reliability_fault_tolerance: {
            score: 3.9,
            feedback: 'Basic fault tolerance understanding',
            strengths: ['Redundancy awareness'],
            areas_for_improvement: ['Circuit breakers', 'Retry strategies'],
            confidence: 3.8
        },
        communication_thought_process: {
            score: 4.3,
            feedback: 'Clear communication and logical thinking',
            strengths: ['Structured approach', 'Good explanations'],
            areas_for_improvement: ['Consider alternatives'],
            confidence: 4.2
        }
    },
    detailed_feedback: 'Overall excellent performance with room for improvement in specific areas.',
    summary: 'Strong system design skills with excellent communication.',
    recommendations: ['Focus on edge cases', 'Consider failure scenarios', 'Dive deeper into trade-offs'],
    next_steps: ['Practice failure mode analysis', 'Study scalability patterns', 'Review reliability patterns'],
    timestamp: '2025-08-12T10:00:00Z'
}

describe('AssessmentPanel', () => {
    it('renders loading state when isLoading is true', () => {
        render(<AssessmentPanel isLoading={true} assessment={null} />)

        expect(screen.getByText('Analyzing your performance...')).toBeInTheDocument()
        expect(screen.getByText('Analyzing your performance...')).toBeInTheDocument() // loading text
    })

    it('renders empty state when no assessment', () => {
        render(<AssessmentPanel assessment={null} isLoading={false} />)

        expect(screen.getByText('No Assessment Yet')).toBeInTheDocument()
        expect(screen.getByText('Complete a learning session and request an assessment to see your progress.')).toBeInTheDocument()
    })

    it('renders assessment results when assessment is provided', () => {
        render(<AssessmentPanel assessment={mockAssessment} isLoading={false} />)

        // Overall score
        expect(screen.getByText('Overall Assessment Score')).toBeInTheDocument()
        expect(screen.getByText('4.2/5.0')).toBeInTheDocument()
        expect(screen.getByText('Confidence: 4.1/5.0')).toBeInTheDocument()
        expect(screen.getByText('Strong system design skills with excellent communication.')).toBeInTheDocument()

        // Dimension scores
        expect(screen.getByText('Detailed Dimension Scores')).toBeInTheDocument()
        expect(screen.getByText('Requirements Analysis')).toBeInTheDocument()
        expect(screen.getByText('System Architecture')).toBeInTheDocument()

        // Recommendations
        expect(screen.getByText('Actionable Recommendations')).toBeInTheDocument()
        expect(screen.getByText('Focus on edge cases')).toBeInTheDocument()
        expect(screen.getByText('Practice failure mode analysis')).toBeInTheDocument()
    })

    it('displays all 6 dimensions correctly', () => {
        render(<AssessmentPanel assessment={mockAssessment} isLoading={false} />)

        const dimensions = [
            'Requirements Analysis',
            'System Architecture',
            'Technical Deep Dive',
            'Scale & Performance',
            'Reliability & Fault Tolerance',
            'Communication & Thought Process'
        ]

        dimensions.forEach(dimension => {
            expect(screen.getByText(dimension)).toBeInTheDocument()
        })
    })

    it('shows strengths and areas for improvement for each dimension', () => {
        render(<AssessmentPanel assessment={mockAssessment} isLoading={false} />)

        // Check strengths
        expect(screen.getByText('Clear problem identification')).toBeInTheDocument()
        expect(screen.getByText('Clean separation of concerns')).toBeInTheDocument()

        // Check areas for improvement
        expect(screen.getByText('Consider edge cases')).toBeInTheDocument()
        expect(screen.getByText('Consider failure modes')).toBeInTheDocument()
    })

    it('displays assessment metadata', () => {
        render(<AssessmentPanel assessment={mockAssessment} isLoading={false} />)

        expect(screen.getByText(/Assessment ID: test-123/)).toBeInTheDocument()
        expect(screen.getByText(/Completed:/)).toBeInTheDocument()
    })

    it('applies custom className', () => {
        render(
            <AssessmentPanel
                assessment={mockAssessment}
                isLoading={false}
                className="custom-class"
            />
        )

        const panel = screen.getByTestId('assessment-panel')
        expect(panel).toHaveClass('custom-class')
    })
})
