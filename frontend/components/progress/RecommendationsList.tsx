'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Lightbulb, Target, AlertCircle, CheckCircle } from 'lucide-react'
import { Recommendation } from '../ProgressDashboard'

interface RecommendationsListProps {
    recommendations: Recommendation[]
}

const dimensionLabels = {
    requirements_analysis: 'Requirements Analysis',
    system_architecture: 'System Architecture',
    technical_deep_dive: 'Technical Deep Dive', 
    scale_performance: 'Scale & Performance',
    reliability_fault_tolerance: 'Reliability & Fault Tolerance',
    communication_thought_process: 'Communication & Thought Process'
}

const getPriorityColor = (priority: number) => {
    switch (priority) {
        case 5:
        case 4:
            return 'bg-red-100 text-red-800 border-red-200'
        case 3:
            return 'bg-yellow-100 text-yellow-800 border-yellow-200'
        case 2:
        case 1:
            return 'bg-green-100 text-green-800 border-green-200'
        default:
            return 'bg-gray-100 text-gray-800 border-gray-200'
    }
}

const getPriorityLabel = (priority: number) => {
    switch (priority) {
        case 5:
            return 'Critical'
        case 4:
            return 'High'
        case 3:
            return 'Medium'
        case 2:
            return 'Low'
        case 1:
            return 'Optional'
        default:
            return 'Normal'
    }
}

const getPriorityIcon = (priority: number) => {
    switch (priority) {
        case 5:
        case 4:
            return <AlertCircle className="h-4 w-4" />
        case 3:
            return <Target className="h-4 w-4" />
        case 2:
        case 1:
            return <CheckCircle className="h-4 w-4" />
        default:
            return <Lightbulb className="h-4 w-4" />
    }
}

export function RecommendationsList({ recommendations }: RecommendationsListProps) {
    if (!recommendations || recommendations.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="h-5 w-5" />
                        Personalized Insights
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8 text-gray-500">
                        <Lightbulb className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p className="text-lg mb-2">No insights available yet</p>
                        <p className="text-sm">
                            Complete more assessments to receive personalized recommendations 
                            based on your learning patterns and performance.
                        </p>
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Sort recommendations by priority (highest first)
    const sortedRecommendations = [...recommendations].sort((a, b) => b.priority - a.priority)
    
    // Group recommendations by priority
    const highPriority = sortedRecommendations.filter(r => r.priority >= 4)
    const mediumPriority = sortedRecommendations.filter(r => r.priority === 3)
    const lowPriority = sortedRecommendations.filter(r => r.priority <= 2)

    return (
        <div className="space-y-6">
            {/* Header */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="h-5 w-5" />
                        Personalized Learning Insights
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-600">
                        Based on your assessment history and performance patterns, here are targeted 
                        recommendations to help you improve your system design skills.
                    </p>
                </CardContent>
            </Card>

            {/* High Priority Recommendations */}
            {highPriority.length > 0 && (
                <Card className="border-red-200 bg-red-50">
                    <CardHeader>
                        <CardTitle className="text-red-800 flex items-center gap-2">
                            <AlertCircle className="h-5 w-5" />
                            Focus Areas ({highPriority.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {highPriority.map((rec, index) => (
                            <div key={index} className="p-4 bg-white border border-red-200 rounded-lg">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {getPriorityIcon(rec.priority)}
                                        {rec.dimension && (
                                            <Badge variant="outline" className="text-xs">
                                                {dimensionLabels[rec.dimension as keyof typeof dimensionLabels] || rec.dimension}
                                            </Badge>
                                        )}
                                    </div>
                                    <Badge className={getPriorityColor(rec.priority)}>
                                        {getPriorityLabel(rec.priority)}
                                    </Badge>
                                </div>
                                <p className="text-gray-800 leading-relaxed">{rec.description}</p>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            )}

            {/* Medium Priority Recommendations */}
            {mediumPriority.length > 0 && (
                <Card className="border-yellow-200 bg-yellow-50">
                    <CardHeader>
                        <CardTitle className="text-yellow-800 flex items-center gap-2">
                            <Target className="h-5 w-5" />
                            Improvement Opportunities ({mediumPriority.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {mediumPriority.map((rec, index) => (
                            <div key={index} className="p-4 bg-white border border-yellow-200 rounded-lg">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {getPriorityIcon(rec.priority)}
                                        {rec.dimension && (
                                            <Badge variant="outline" className="text-xs">
                                                {dimensionLabels[rec.dimension as keyof typeof dimensionLabels] || rec.dimension}
                                            </Badge>
                                        )}
                                    </div>
                                    <Badge className={getPriorityColor(rec.priority)}>
                                        {getPriorityLabel(rec.priority)}
                                    </Badge>
                                </div>
                                <p className="text-gray-800 leading-relaxed">{rec.description}</p>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            )}

            {/* Low Priority Recommendations */}
            {lowPriority.length > 0 && (
                <Card className="border-green-200 bg-green-50">
                    <CardHeader>
                        <CardTitle className="text-green-800 flex items-center gap-2">
                            <CheckCircle className="h-5 w-5" />
                            Enhancement Suggestions ({lowPriority.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {lowPriority.map((rec, index) => (
                            <div key={index} className="p-4 bg-white border border-green-200 rounded-lg">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {getPriorityIcon(rec.priority)}
                                        {rec.dimension && (
                                            <Badge variant="outline" className="text-xs">
                                                {dimensionLabels[rec.dimension as keyof typeof dimensionLabels] || rec.dimension}
                                            </Badge>
                                        )}
                                    </div>
                                    <Badge className={getPriorityColor(rec.priority)}>
                                        {getPriorityLabel(rec.priority)}
                                    </Badge>
                                </div>
                                <p className="text-gray-800 leading-relaxed">{rec.description}</p>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            )}

            {/* Summary */}
            <Card>
                <CardContent className="p-4">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                        <span>Total Recommendations: {recommendations.length}</span>
                        <div className="flex items-center gap-4">
                            {highPriority.length > 0 && (
                                <span className="flex items-center gap-1 text-red-600">
                                    <AlertCircle className="h-3 w-3" />
                                    {highPriority.length} High Priority
                                </span>
                            )}
                            {mediumPriority.length > 0 && (
                                <span className="flex items-center gap-1 text-yellow-600">
                                    <Target className="h-3 w-3" />
                                    {mediumPriority.length} Medium Priority
                                </span>
                            )}
                            {lowPriority.length > 0 && (
                                <span className="flex items-center gap-1 text-green-600">
                                    <CheckCircle className="h-3 w-3" />
                                    {lowPriority.length} Low Priority
                                </span>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}