'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { 
    TrendingUp, 
    TrendingDown, 
    Calendar, 
    Target, 
    Award, 
    Download,
    LineChart,
    BarChart3,
    Trophy,
    CheckCircle
} from 'lucide-react'
import { TimelineChart } from './progress/TimelineChart'
import { TrendAnalysis } from './progress/TrendAnalysis'
import { RecommendationsList } from './progress/RecommendationsList'
import { AchievementBadges } from './progress/AchievementBadges'
import { GoalSetting } from './progress/GoalSetting'

export interface AssessmentDimension {
    REQUIREMENTS_ANALYSIS: 'requirements_analysis'
    SYSTEM_ARCHITECTURE: 'system_architecture' 
    TECHNICAL_DEEP_DIVE: 'technical_deep_dive'
    SCALE_PERFORMANCE: 'scale_performance'
    RELIABILITY_FAULT_TOLERANCE: 'reliability_fault_tolerance'
    COMMUNICATION_THOUGHT_PROCESS: 'communication_thought_process'
}

export interface ProgressPoint {
    date: string
    overall_score: number
    dimension_scores: {
        requirements_analysis: number
        system_architecture: number
        technical_deep_dive: number
        scale_performance: number
        reliability_fault_tolerance: number
        communication_thought_process: number
    }
}

export interface TrendData {
    overall_trend: 'improving' | 'declining' | 'stable'
    improving_dimensions: string[]
    declining_dimensions: string[]
}

export interface Recommendation {
    dimension?: string
    description: string
    priority: number
}

export interface Achievement {
    name: string
    description: string
    earned: boolean
    date?: string
    icon?: string
}

export interface Goal {
    id: string
    description: string
    target_date?: string
    status: 'active' | 'completed' | 'paused'
    progress: number
}

export interface ProgressData {
    timeline: {
        points: ProgressPoint[]
    }
    trends: TrendData
    recommendations: Recommendation[]
    goals: Goal[]
    achievements: Achievement[]
    last_updated: string
}

interface ProgressDashboardProps {
    data: ProgressData
    userId: string
    onExportReport?: () => void
    onSetGoal?: (goal: { description: string; target_date?: string }) => Promise<void>
    onUpdateGoal?: (goalId: string, progress: number, status?: string) => Promise<void>
}

export function ProgressDashboard({ 
    data, 
    userId, 
    onExportReport, 
    onSetGoal,
    onUpdateGoal 
}: ProgressDashboardProps) {
    const [selectedDataPoint, setSelectedDataPoint] = useState<ProgressPoint | null>(null)
    const [isExporting, setIsExporting] = useState(false)

    const handleExportReport = async () => {
        if (!onExportReport) return
        
        setIsExporting(true)
        try {
            await onExportReport()
        } catch (error) {
            console.error('Failed to export report:', error)
        } finally {
            setIsExporting(false)
        }
    }

    const getOverallTrend = () => {
        if (data.timeline.points.length < 2) return null
        
        const recent = data.timeline.points.slice(-5)
        if (recent.length < 2) return null
        
        const firstScore = recent[0].overall_score
        const lastScore = recent[recent.length - 1].overall_score
        const change = lastScore - firstScore
        
        return {
            direction: change > 0.1 ? 'up' : change < -0.1 ? 'down' : 'stable',
            change: Math.abs(change),
            percentage: Math.abs((change / firstScore) * 100)
        }
    }

    const trend = getOverallTrend()

    return (
        <div className="space-y-6 p-6" data-testid="progress-dashboard">
            {/* Header with Export */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Learning Progress</h2>
                    <p className="text-gray-600">Track your system design mastery over time</p>
                </div>
                <Button 
                    onClick={handleExportReport}
                    disabled={isExporting}
                    className="flex items-center gap-2"
                    data-testid="export-report-btn"
                >
                    <Download className="h-4 w-4" />
                    {isExporting ? 'Exporting...' : 'Export Report'}
                </Button>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Current Score</p>
                                <p className="text-2xl font-bold text-blue-600">
                                    {data.timeline.points.length > 0 ? 
                                        data.timeline.points[data.timeline.points.length - 1].overall_score.toFixed(1) : 
                                        'N/A'
                                    }/5.0
                                </p>
                            </div>
                            <BarChart3 className="h-8 w-8 text-blue-600" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Total Assessments</p>
                                <p className="text-2xl font-bold text-green-600">
                                    {data.timeline.points.length}
                                </p>
                            </div>
                            <LineChart className="h-8 w-8 text-green-600" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Trend</p>
                                <div className="flex items-center gap-1">
                                    {trend ? (
                                        <>
                                            {trend.direction === 'up' && <TrendingUp className="h-4 w-4 text-green-600" />}
                                            {trend.direction === 'down' && <TrendingDown className="h-4 w-4 text-red-600" />}
                                            <span className={`text-sm font-medium ${
                                                trend.direction === 'up' ? 'text-green-600' :
                                                trend.direction === 'down' ? 'text-red-600' : 
                                                'text-gray-600'
                                            }`}>
                                                {trend.direction === 'up' ? 'Improving' :
                                                 trend.direction === 'down' ? 'Declining' :
                                                 'Stable'}
                                            </span>
                                        </>
                                    ) : (
                                        <span className="text-sm text-gray-600">N/A</span>
                                    )}
                                </div>
                            </div>
                            {trend && trend.direction !== 'stable' && (
                                <div className="text-right">
                                    <p className={`text-lg font-bold ${
                                        trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
                                    }`}>
                                        {trend.direction === 'up' ? '+' : ''}{trend.change.toFixed(1)}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {trend.percentage.toFixed(1)}%
                                    </p>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Achievements</p>
                                <p className="text-2xl font-bold text-purple-600">
                                    {data.achievements?.filter(a => a.earned).length || 0}
                                </p>
                            </div>
                            <Trophy className="h-8 w-8 text-purple-600" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content Tabs */}
            <Tabs defaultValue="timeline" className="space-y-4">
                <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="timeline" className="flex items-center gap-2">
                        <LineChart className="h-4 w-4" />
                        Timeline
                    </TabsTrigger>
                    <TabsTrigger value="trends" className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Trends
                    </TabsTrigger>
                    <TabsTrigger value="recommendations" className="flex items-center gap-2">
                        <Target className="h-4 w-4" />
                        Insights
                    </TabsTrigger>
                    <TabsTrigger value="achievements" className="flex items-center gap-2">
                        <Award className="h-4 w-4" />
                        Achievements
                    </TabsTrigger>
                    <TabsTrigger value="goals" className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        Goals
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="timeline" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <LineChart className="h-5 w-5" />
                                Progress Timeline
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <TimelineChart 
                                data={data.timeline.points}
                                onPointSelect={setSelectedDataPoint}
                                selectedPoint={selectedDataPoint}
                            />
                        </CardContent>
                    </Card>

                    {/* Selected Point Details */}
                    {selectedDataPoint && (
                        <Card data-testid="assessment-details">
                            <CardHeader>
                                <CardTitle>Assessment Details - {selectedDataPoint.date}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-gray-600">Requirements Analysis</p>
                                        <p className="text-lg font-bold text-blue-600">
                                            {selectedDataPoint.dimension_scores.requirements_analysis.toFixed(1)}/5
                                        </p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-gray-600">System Architecture</p>
                                        <p className="text-lg font-bold text-green-600">
                                            {selectedDataPoint.dimension_scores.system_architecture.toFixed(1)}/5
                                        </p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-gray-600">Technical Deep Dive</p>
                                        <p className="text-lg font-bold text-purple-600">
                                            {selectedDataPoint.dimension_scores.technical_deep_dive.toFixed(1)}/5
                                        </p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-gray-600">Scale & Performance</p>
                                        <p className="text-lg font-bold text-orange-600">
                                            {selectedDataPoint.dimension_scores.scale_performance.toFixed(1)}/5
                                        </p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-gray-600">Reliability</p>
                                        <p className="text-lg font-bold text-red-600">
                                            {selectedDataPoint.dimension_scores.reliability_fault_tolerance.toFixed(1)}/5
                                        </p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-gray-600">Communication</p>
                                        <p className="text-lg font-bold text-indigo-600">
                                            {selectedDataPoint.dimension_scores.communication_thought_process.toFixed(1)}/5
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>

                <TabsContent value="trends" className="space-y-4">
                    <TrendAnalysis data={data.trends} />
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4">
                    <RecommendationsList recommendations={data.recommendations} />
                </TabsContent>

                <TabsContent value="achievements" className="space-y-4">
                    <AchievementBadges achievements={data.achievements || []} />
                </TabsContent>

                <TabsContent value="goals" className="space-y-4">
                    <GoalSetting 
                        goals={data.goals || []} 
                        onSetGoal={onSetGoal}
                        onUpdateGoal={onUpdateGoal}
                    />
                </TabsContent>
            </Tabs>

            {/* Last Updated */}
            <div className="text-center text-sm text-gray-500 border-t pt-4">
                Last updated: {new Date(data.last_updated).toLocaleString()}
            </div>
        </div>
    )
}