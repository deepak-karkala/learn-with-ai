'use client'

import React from 'react'
import { ProgressPoint } from '../ProgressDashboard'

interface TimelineChartProps {
    data: ProgressPoint[]
    onPointSelect?: (point: ProgressPoint) => void
    selectedPoint?: ProgressPoint | null
}

export function TimelineChart({ data, onPointSelect, selectedPoint }: TimelineChartProps) {
    if (!data || data.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center text-gray-500" data-testid="timeline-chart">
                <div className="text-center">
                    <p>No progress data available yet.</p>
                    <p className="text-sm">Complete an assessment to see your progress timeline.</p>
                </div>
            </div>
        )
    }

    // Calculate chart dimensions and scaling
    const chartHeight = 200
    const chartWidth = 600
    const padding = 40

    const maxScore = 5.0
    const minScore = 0.0
    
    // Scale functions
    const xScale = (index: number) => {
        if (data.length === 1) return chartWidth / 2 // Center single point
        return padding + (index / (data.length - 1)) * (chartWidth - 2 * padding)
    }
    const yScale = (score: number) => chartHeight - padding - ((score - minScore) / (maxScore - minScore)) * (chartHeight - 2 * padding)

    // Generate SVG path for overall score line
    const overallScorePath = data.map((point, index) => {
        const x = xScale(index)
        const y = yScale(point.overall_score)
        return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
    }).join(' ')

    // Generate dimension lines
    const dimensionKeys = [
        'requirements_analysis',
        'system_architecture',
        'technical_deep_dive',
        'scale_performance',
        'reliability_fault_tolerance',
        'communication_thought_process'
    ] as const

    const dimensionColors = {
        requirements_analysis: '#3B82F6',
        system_architecture: '#10B981',
        technical_deep_dive: '#8B5CF6',
        scale_performance: '#F59E0B',
        reliability_fault_tolerance: '#EF4444',
        communication_thought_process: '#6366F1'
    }

    const dimensionLabels = {
        requirements_analysis: 'Requirements',
        system_architecture: 'Architecture',
        technical_deep_dive: 'Technical',
        scale_performance: 'Scale',
        reliability_fault_tolerance: 'Reliability',
        communication_thought_process: 'Communication'
    }

    return (
        <div className="space-y-4" data-testid="timeline-chart">
            {/* Chart */}
            <div className="bg-white border rounded-lg p-4 overflow-x-auto">
                <svg width={chartWidth} height={chartHeight} className="w-full h-auto min-w-[600px]">
                    {/* Grid lines */}
                    {[1, 2, 3, 4, 5].map(score => (
                        <line
                            key={score}
                            x1={padding}
                            y1={yScale(score)}
                            x2={chartWidth - padding}
                            y2={yScale(score)}
                            stroke="#E5E7EB"
                            strokeDasharray="2,2"
                        />
                    ))}
                    
                    {/* Y-axis labels */}
                    {[1, 2, 3, 4, 5].map(score => (
                        <text
                            key={score}
                            x={padding - 10}
                            y={yScale(score) + 4}
                            textAnchor="end"
                            fontSize="12"
                            fill="#6B7280"
                        >
                            {score}
                        </text>
                    ))}

                    {/* Overall score line */}
                    <path
                        d={overallScorePath}
                        stroke="#1F2937"
                        strokeWidth="3"
                        fill="none"
                    />

                    {/* Dimension lines (lighter) */}
                    {dimensionKeys.map(dimension => {
                        const path = data.map((point, index) => {
                            const x = xScale(index)
                            const y = yScale(point.dimension_scores[dimension])
                            return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
                        }).join(' ')

                        return (
                            <path
                                key={dimension}
                                d={path}
                                stroke={dimensionColors[dimension]}
                                strokeWidth="1"
                                fill="none"
                                opacity="0.6"
                            />
                        )
                    })}

                    {/* Data points */}
                    {data.map((point, index) => (
                        <circle
                            key={index}
                            cx={xScale(index)}
                            cy={yScale(point.overall_score)}
                            r="6"
                            fill={selectedPoint === point ? "#DC2626" : "#1F2937"}
                            stroke="white"
                            strokeWidth="2"
                            className="cursor-pointer hover:r-8 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500"
                            onClick={() => onPointSelect?.(point)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault()
                                    onPointSelect?.(point)
                                }
                            }}
                            tabIndex={0}
                            role="button"
                            aria-label={`Data point for ${point.date}, score ${point.overall_score}`}
                            data-testid={`data-point-${index}`}
                        />
                    ))}

                    {/* X-axis labels */}
                    {data.map((point, index) => (
                        <text
                            key={index}
                            x={xScale(index)}
                            y={chartHeight - 10}
                            textAnchor="middle"
                            fontSize="10"
                            fill="#6B7280"
                        >
                            {new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </text>
                    ))}
                </svg>
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-4 justify-center">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5 bg-gray-800"></div>
                    <span className="text-sm text-gray-600">Overall Score</span>
                </div>
                {dimensionKeys.map(dimension => (
                    <div key={dimension} className="flex items-center gap-2">
                        <div 
                            className="w-4 h-0.5 opacity-60" 
                            style={{ backgroundColor: dimensionColors[dimension] }}
                        ></div>
                        <span className="text-sm text-gray-600">
                            {dimensionLabels[dimension]}
                        </span>
                    </div>
                ))}
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="text-center">
                    <p className="text-sm text-gray-600">Best Score</p>
                    <p className="text-lg font-bold text-green-600">
                        {Math.max(...data.map(d => d.overall_score)).toFixed(1)}
                    </p>
                </div>
                <div className="text-center">
                    <p className="text-sm text-gray-600">Average</p>
                    <p className="text-lg font-bold text-blue-600">
                        {(data.reduce((sum, d) => sum + d.overall_score, 0) / data.length).toFixed(1)}
                    </p>
                </div>
                <div className="text-center">
                    <p className="text-sm text-gray-600">Latest</p>
                    <p className="text-lg font-bold text-purple-600">
                        {data[data.length - 1].overall_score.toFixed(1)}
                    </p>
                </div>
            </div>
        </div>
    )
}