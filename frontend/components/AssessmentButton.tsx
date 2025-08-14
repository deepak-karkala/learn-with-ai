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
            className={`bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 px-6 py-3 ${className}`}
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
