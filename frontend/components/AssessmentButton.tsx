'use client'

import React from 'react'
import { Button } from './ui/button'
import { Target, Loader2 } from 'lucide-react'

interface AssessmentButtonProps {
    onRequestAssessment: () => void
    isLoading?: boolean
    disabled?: boolean
    className?: string
}

export function AssessmentButton({
    onRequestAssessment,
    isLoading = false,
    disabled = false,
    className = ''
}: AssessmentButtonProps) {
    return (
        <Button
            onClick={onRequestAssessment}
            disabled={disabled || isLoading}
            className={`bg-purple-600 hover:bg-purple-700 text-white font-semibold ${className}`}
            data-testid="assessment-button"
        >
            {isLoading ? (
                <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Getting Assessment...
                </>
            ) : (
                <>
                    <Target className="h-4 w-4 mr-2" />
                    🎯 Get Assessment
                </>
            )}
        </Button>
    )
}
