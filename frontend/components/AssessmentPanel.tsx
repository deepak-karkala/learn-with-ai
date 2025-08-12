'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { TrendingUp, TrendingDown, Minus, Star, Target } from 'lucide-react'

interface DimensionScore {
    score: number
    feedback: string
    strengths: string[]
    areas_for_improvement: string[]
    confidence: number
}

interface AssessmentData {
    assessment_id: string
    user_id: string
    overall_score: number
    confidence_score: number
    dimension_scores: {
        requirements_analysis: DimensionScore
        system_architecture: DimensionScore
        technical_deep_dive: DimensionScore
        scale_performance: DimensionScore
        reliability_fault_tolerance: DimensionScore
        communication_thought_process: DimensionScore
    }
    detailed_feedback: string
    summary: string
    recommendations: string[]
    next_steps: string[]
    timestamp: string
}

interface AssessmentPanelProps {
    assessment: AssessmentData | null
    isLoading?: boolean
    className?: string
}

const dimensionLabels = {
    requirements_analysis: 'Requirements Analysis',
    system_architecture: 'System Architecture',
    technical_deep_dive: 'Technical Deep Dive',
    scale_performance: 'Scale & Performance',
    reliability_fault_tolerance: 'Reliability & Fault Tolerance',
    communication_thought_process: 'Communication & Thought Process'
}

const getScoreColor = (score: number) => {
    if (score >= 4.5) return 'bg-green-100 text-green-800 border-green-200'
    if (score >= 3.5) return 'bg-blue-100 text-blue-800 border-blue-200'
    if (score >= 2.5) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-red-100 text-red-800 border-red-200'
}

const getConfidenceColor = (confidence: number) => {
    if (confidence >= 4.5) return 'text-green-600'
    if (confidence >= 3.5) return 'text-blue-600'
    if (confidence >= 2.5) return 'text-yellow-600'
    return 'text-red-600'
}

const getTrendIcon = (score: number) => {
    if (score >= 4.5) return <TrendingUp className="h-4 w-4 text-green-600" />
    if (score >= 3.5) return <TrendingUp className="h-4 w-4 text-blue-600" />
    if (score >= 2.5) return <Minus className="h-4 w-4 text-yellow-600" />
    return <TrendingDown className="h-4 w-4 text-red-600" />
}

export function AssessmentPanel({
    assessment,
    isLoading = false,
    className = ''
}: AssessmentPanelProps) {
    if (isLoading) {
        return (
            <div className={`flex items-center justify-center p-8 ${className}`}>
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Analyzing your performance...</p>
                </div>
            </div>
        )
    }

    if (!assessment) {
        return (
            <div className={`text-center p-8 text-gray-500 ${className}`}>
                <Target className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-semibold mb-2">No Assessment Yet</h3>
                <p>Complete a learning session and request an assessment to see your progress.</p>
            </div>
        )
    }

    return (
        <div className={`space-y-6 ${className}`} data-testid="assessment-panel">
            {/* Overall Score Header */}
            <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
                <CardHeader className="text-center">
                    <CardTitle className="flex items-center justify-center gap-2">
                        <Star className="h-6 w-6 text-yellow-500" />
                        Overall Assessment Score
                    </CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                    <div className="text-4xl font-bold text-purple-600 mb-2">
                        {assessment.overall_score.toFixed(1)}/5.0
                    </div>
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <Badge className={getScoreColor(assessment.overall_score)}>
                            Confidence: {assessment.confidence_score.toFixed(1)}/5.0
                        </Badge>
                    </div>
                    <p className="text-gray-700 text-lg">{assessment.summary}</p>
                </CardContent>
            </Card>

            {/* Dimension Scores */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Target className="h-5 w-5" />
                        Detailed Dimension Scores
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4">
                        {Object.entries(assessment.dimension_scores).map(([key, dimension]) => (
                            <div key={key} className="border rounded-lg p-4 bg-gray-50">
                                <div className="flex items-center justify-between mb-3">
                                    <h4 className="font-semibold text-gray-800">
                                        {dimensionLabels[key as keyof typeof dimensionLabels]}
                                    </h4>
                                    <div className="flex items-center gap-2">
                                        {getTrendIcon(dimension.score)}
                                        <Badge className={getScoreColor(dimension.score)}>
                                            {dimension.score.toFixed(1)}/5.0
                                        </Badge>
                                        <span className={`text-sm ${getConfidenceColor(dimension.confidence)}`}>
                                            Confidence: {dimension.confidence.toFixed(1)}
                                        </span>
                                    </div>
                                </div>

                                <p className="text-gray-700 mb-3">{dimension.feedback}</p>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                        <h5 className="font-medium text-green-700 mb-2">Strengths</h5>
                                        <ul className="space-y-1">
                                            {dimension.strengths.map((strength, index) => (
                                                <li key={index} className="text-sm text-green-600 flex items-center gap-1">
                                                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                                    {strength}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    <div>
                                        <h5 className="font-medium text-orange-700 mb-2">Areas for Improvement</h5>
                                        <ul className="space-y-1">
                                            {dimension.areas_for_improvement.map((area, index) => (
                                                <li key={index} className="text-sm text-orange-600 flex items-center gap-1">
                                                    <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                                                    {area}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
                <CardHeader>
                    <CardTitle>Actionable Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div>
                            <h4 className="font-medium text-gray-800 mb-2">Key Recommendations</h4>
                            <ul className="space-y-2">
                                {assessment.recommendations.map((rec, index) => (
                                    <li key={index} className="flex items-start gap-2">
                                        <div className="w-2 h-2 bg-purple-400 rounded-full mt-2 flex-shrink-0"></div>
                                        <span className="text-gray-700">{rec}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div>
                            <h4 className="font-medium text-gray-800 mb-2">Next Steps</h4>
                            <ul className="space-y-2">
                                {assessment.next_steps.map((step, index) => (
                                    <li key={index} className="flex items-start gap-2">
                                        <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                                        <span className="text-gray-700">{step}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Assessment Metadata */}
            <Card className="bg-gray-50">
                <CardContent className="pt-6">
                    <div className="text-sm text-gray-500 text-center">
                        Assessment ID: {assessment.assessment_id} •
                        Completed: {new Date(assessment.timestamp).toLocaleDateString()}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
