'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react'
import { TrendData } from '../ProgressDashboard'

interface TrendAnalysisProps {
    data: TrendData
}

const dimensionLabels = {
    requirements_analysis: 'Requirements Analysis',
    system_architecture: 'System Architecture', 
    technical_deep_dive: 'Technical Deep Dive',
    scale_performance: 'Scale & Performance',
    reliability_fault_tolerance: 'Reliability & Fault Tolerance',
    communication_thought_process: 'Communication & Thought Process'
}

export function TrendAnalysis({ data }: TrendAnalysisProps) {
    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'improving':
                return <TrendingUp className="h-4 w-4 text-green-600" />
            case 'declining':
                return <TrendingDown className="h-4 w-4 text-red-600" />
            default:
                return <Minus className="h-4 w-4 text-gray-600" />
        }
    }

    const getTrendColor = (trend: string) => {
        switch (trend) {
            case 'improving':
                return 'text-green-600 bg-green-50'
            case 'declining':
                return 'text-red-600 bg-red-50'
            default:
                return 'text-gray-600 bg-gray-50'
        }
    }

    return (
        <div className="space-y-6">
            {/* Overall Trend */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="h-5 w-5" />
                        Overall Performance Trend
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-8">
                        <div className="text-center">
                            <div className="flex items-center justify-center mb-4">
                                {getTrendIcon(data.overall_trend)}
                                <Badge 
                                    variant="secondary" 
                                    className={`ml-2 ${getTrendColor(data.overall_trend)}`}
                                >
                                    {data.overall_trend.charAt(0).toUpperCase() + data.overall_trend.slice(1)}
                                </Badge>
                            </div>
                            <p className="text-gray-600">
                                {data.overall_trend === 'improving' && 
                                    "Great progress! Your system design skills are improving across multiple areas."}
                                {data.overall_trend === 'declining' && 
                                    "Your scores have declined recently. Focus on key areas for improvement."}
                                {data.overall_trend === 'stable' && 
                                    "Your performance is stable. Consider targeting specific areas for growth."}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Improving Areas */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-green-700">
                            <TrendingUp className="h-5 w-5" />
                            Improving Areas
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {data.improving_dimensions && data.improving_dimensions.length > 0 ? (
                            data.improving_dimensions.map((dimension) => (
                                <div key={dimension} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                                    <span className="font-medium text-green-800">
                                        {dimensionLabels[dimension as keyof typeof dimensionLabels] || dimension.replace('_', ' ')}
                                    </span>
                                    <TrendingUp className="h-4 w-4 text-green-600" />
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                <p>No improving areas detected yet.</p>
                                <p className="text-sm">Complete more assessments to see trends.</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Areas Needing Attention */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-red-700">
                            <TrendingDown className="h-5 w-5" />
                            Areas Needing Attention
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {data.declining_dimensions && data.declining_dimensions.length > 0 ? (
                            data.declining_dimensions.map((dimension) => (
                                <div key={dimension} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                                    <span className="font-medium text-red-800">
                                        {dimensionLabels[dimension as keyof typeof dimensionLabels] || dimension.replace('_', ' ')}
                                    </span>
                                    <TrendingDown className="h-4 w-4 text-red-600" />
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                <TrendingDown className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                <p>No declining areas detected.</p>
                                <p className="text-sm">Keep up the great work!</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Insights and Recommendations */}
            <Card>
                <CardHeader>
                    <CardTitle>Key Insights</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {data.improving_dimensions && data.improving_dimensions.length > 0 && (
                        <div className="p-4 bg-green-50 border-l-4 border-green-400 rounded-r-lg">
                            <h4 className="font-semibold text-green-800 mb-2">Strengths to Leverage</h4>
                            <p className="text-green-700 text-sm">
                                You're showing strong improvement in{' '}
                                {data.improving_dimensions.length === 1 
                                    ? (dimensionLabels[data.improving_dimensions[0] as keyof typeof dimensionLabels] || data.improving_dimensions[0])
                                    : data.improving_dimensions.length === 2
                                    ? `${dimensionLabels[data.improving_dimensions[0] as keyof typeof dimensionLabels] || data.improving_dimensions[0]} and ${dimensionLabels[data.improving_dimensions[1] as keyof typeof dimensionLabels] || data.improving_dimensions[1]}`
                                    : `${data.improving_dimensions.length} areas`
                                }. Continue building on these strengths!
                            </p>
                        </div>
                    )}

                    {data.declining_dimensions && data.declining_dimensions.length > 0 && (
                        <div className="p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg">
                            <h4 className="font-semibold text-yellow-800 mb-2">Areas for Focus</h4>
                            <p className="text-yellow-700 text-sm">
                                Consider dedicating more practice time to{' '}
                                {data.declining_dimensions.length === 1 
                                    ? (dimensionLabels[data.declining_dimensions[0] as keyof typeof dimensionLabels] || data.declining_dimensions[0])
                                    : data.declining_dimensions.length === 2
                                    ? `${dimensionLabels[data.declining_dimensions[0] as keyof typeof dimensionLabels] || data.declining_dimensions[0]} and ${dimensionLabels[data.declining_dimensions[1] as keyof typeof dimensionLabels] || data.declining_dimensions[1]}`
                                    : `${data.declining_dimensions.length} key areas`
                                }. Targeted practice can help turn these around.
                            </p>
                        </div>
                    )}

                    {(!data.improving_dimensions || data.improving_dimensions.length === 0) &&
                     (!data.declining_dimensions || data.declining_dimensions.length === 0) && (
                        <div className="p-4 bg-blue-50 border-l-4 border-blue-400 rounded-r-lg">
                            <h4 className="font-semibold text-blue-800 mb-2">Steady Progress</h4>
                            <p className="text-blue-700 text-sm">
                                Your performance is consistent across all dimensions. Consider challenging yourself 
                                with more complex system design scenarios to accelerate growth.
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}