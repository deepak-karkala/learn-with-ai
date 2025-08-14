'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Badge } from '../ui/badge'
import { 
    Target, 
    Plus, 
    Calendar, 
    CheckCircle, 
    Clock, 
    Pause,
    Trash2,
    Edit
} from 'lucide-react'
import { Goal } from '../ProgressDashboard'

interface GoalSettingProps {
    goals: Goal[]
    onSetGoal?: (goal: { description: string; target_date?: string }) => Promise<void>
    onUpdateGoal?: (goalId: string, progress: number, status?: string) => Promise<void>
}

const getStatusIcon = (status: string) => {
    switch (status) {
        case 'completed':
            return <CheckCircle className="h-4 w-4 text-green-600" />
        case 'paused':
            return <Pause className="h-4 w-4 text-yellow-600" />
        default:
            return <Clock className="h-4 w-4 text-blue-600" />
    }
}

const getStatusColor = (status: string) => {
    switch (status) {
        case 'completed':
            return 'bg-green-100 text-green-800 border-green-200'
        case 'paused':
            return 'bg-yellow-100 text-yellow-800 border-yellow-200'
        default:
            return 'bg-blue-100 text-blue-800 border-blue-200'
    }
}

export function GoalSetting({ goals, onSetGoal, onUpdateGoal }: GoalSettingProps) {
    const [showAddGoal, setShowAddGoal] = useState(false)
    const [newGoalDescription, setNewGoalDescription] = useState('')
    const [newGoalDate, setNewGoalDate] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [editingGoal, setEditingGoal] = useState<string | null>(null)
    const [editProgress, setEditProgress] = useState<number>(0)

    const handleAddGoal = async () => {
        if (!newGoalDescription.trim() || !onSetGoal) return

        setIsSubmitting(true)
        try {
            await onSetGoal({
                description: newGoalDescription.trim(),
                target_date: newGoalDate || undefined
            })
            setNewGoalDescription('')
            setNewGoalDate('')
            setShowAddGoal(false)
        } catch (error) {
            console.error('Failed to set goal:', error)
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleUpdateProgress = async (goalId: string, newProgress: number) => {
        if (!onUpdateGoal) return

        try {
            const newStatus = newProgress >= 100 ? 'completed' : 'active'
            await onUpdateGoal(goalId, newProgress, newStatus)
            setEditingGoal(null)
        } catch (error) {
            console.error('Failed to update goal:', error)
        }
    }

    const startEditingProgress = (goal: Goal) => {
        setEditingGoal(goal.id)
        setEditProgress(goal.progress)
    }

    const activeGoals = goals.filter(g => g.status === 'active')
    const completedGoals = goals.filter(g => g.status === 'completed')
    const pausedGoals = goals.filter(g => g.status === 'paused')

    return (
        <div className="space-y-6">
            {/* Header */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Target className="h-5 w-5" />
                            Learning Goals
                        </div>
                        <Button
                            onClick={() => setShowAddGoal(!showAddGoal)}
                            size="sm"
                            className="flex items-center gap-2"
                        >
                            <Plus className="h-4 w-4" />
                            Add Goal
                        </Button>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                            <p className="text-2xl font-bold text-blue-600">{activeGoals.length}</p>
                            <p className="text-sm text-gray-600">Active Goals</p>
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-green-600">{completedGoals.length}</p>
                            <p className="text-sm text-gray-600">Completed</p>
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-yellow-600">{pausedGoals.length}</p>
                            <p className="text-sm text-gray-600">On Hold</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Add New Goal */}
            {showAddGoal && (
                <Card className="border-blue-200 bg-blue-50">
                    <CardHeader>
                        <CardTitle className="text-blue-800">Set New Learning Goal</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Goal Description
                            </label>
                            <Input
                                placeholder="e.g., Achieve 4.5+ overall score in system design assessments"
                                value={newGoalDescription}
                                onChange={(e) => setNewGoalDescription(e.target.value)}
                                maxLength={200}
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                {newGoalDescription.length}/200 characters
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Target Date (Optional)
                            </label>
                            <Input
                                type="date"
                                value={newGoalDate}
                                onChange={(e) => setNewGoalDate(e.target.value)}
                                min={new Date().toISOString().split('T')[0]}
                            />
                        </div>

                        <div className="flex gap-2">
                            <Button
                                onClick={handleAddGoal}
                                disabled={!newGoalDescription.trim() || isSubmitting}
                                className="flex-1"
                            >
                                {isSubmitting ? 'Setting Goal...' : 'Set Goal'}
                            </Button>
                            <Button
                                onClick={() => {
                                    setShowAddGoal(false)
                                    setNewGoalDescription('')
                                    setNewGoalDate('')
                                }}
                                variant="outline"
                            >
                                Cancel
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Active Goals */}
            {activeGoals.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold mb-4 text-blue-700 flex items-center gap-2">
                        <Target className="h-5 w-5" />
                        Active Goals ({activeGoals.length})
                    </h3>
                    <div className="space-y-4">
                        {activeGoals.map((goal) => (
                            <Card key={goal.id} className="border-blue-200">
                                <CardContent className="p-4">
                                    <div className="space-y-3">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <p className="font-medium text-gray-900 mb-1">
                                                    {goal.description}
                                                </p>
                                                {goal.target_date && (
                                                    <p className="text-sm text-gray-500 flex items-center gap-1">
                                                        <Calendar className="h-3 w-3" />
                                                        Target: {new Date(goal.target_date).toLocaleDateString()}
                                                    </p>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Badge className={getStatusColor(goal.status)}>
                                                    {getStatusIcon(goal.status)}
                                                    <span className="ml-1 capitalize">{goal.status}</span>
                                                </Badge>
                                            </div>
                                        </div>

                                        {/* Progress Bar */}
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-gray-700">
                                                    Progress
                                                </span>
                                                <span className="text-sm font-medium text-blue-600">
                                                    {goal.progress.toFixed(0)}%
                                                </span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                                    style={{ width: `${goal.progress}%` }}
                                                ></div>
                                            </div>
                                        </div>

                                        {/* Progress Update */}
                                        {editingGoal === goal.id ? (
                                            <div className="flex items-center gap-2">
                                                <Input
                                                    type="number"
                                                    min="0"
                                                    max="100"
                                                    value={editProgress}
                                                    onChange={(e) => setEditProgress(Number(e.target.value))}
                                                    className="w-20"
                                                />
                                                <span className="text-sm text-gray-500">%</span>
                                                <Button
                                                    size="sm"
                                                    onClick={() => handleUpdateProgress(goal.id, editProgress)}
                                                >
                                                    Update
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => setEditingGoal(null)}
                                                >
                                                    Cancel
                                                </Button>
                                            </div>
                                        ) : (
                                            <div className="flex items-center justify-end">
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => startEditingProgress(goal)}
                                                    className="flex items-center gap-1"
                                                >
                                                    <Edit className="h-3 w-3" />
                                                    Update Progress
                                                </Button>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {/* Completed Goals */}
            {completedGoals.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold mb-4 text-green-700 flex items-center gap-2">
                        <CheckCircle className="h-5 w-5" />
                        Completed Goals ({completedGoals.length})
                    </h3>
                    <div className="space-y-4">
                        {completedGoals.map((goal) => (
                            <Card key={goal.id} className="border-green-200 bg-green-50">
                                <CardContent className="p-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="font-medium text-gray-900 mb-1">
                                                {goal.description}
                                            </p>
                                            {goal.target_date && (
                                                <p className="text-sm text-gray-500 flex items-center gap-1">
                                                    <Calendar className="h-3 w-3" />
                                                    Completed by: {new Date(goal.target_date).toLocaleDateString()}
                                                </p>
                                            )}
                                        </div>
                                        <Badge className="bg-green-100 text-green-800 border-green-200">
                                            <CheckCircle className="h-4 w-4 mr-1" />
                                            Completed
                                        </Badge>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {/* No Goals State */}
            {goals.length === 0 && (
                <Card>
                    <CardContent className="p-8">
                        <div className="text-center text-gray-500">
                            <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p className="text-lg mb-2">No learning goals set</p>
                            <p className="text-sm mb-4">
                                Set specific learning goals to track your progress and stay motivated.
                            </p>
                            <Button
                                onClick={() => setShowAddGoal(true)}
                                className="flex items-center gap-2"
                            >
                                <Plus className="h-4 w-4" />
                                Set Your First Goal
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}