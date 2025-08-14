'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from "@/components/ui/button"
import { ArrowLeft, Download } from 'lucide-react'
import { ProgressDashboard, type ProgressData } from '@/components/ProgressDashboard'

// Mock data for development
const mockProgressData: ProgressData = {
  timeline: {
    points: [
      {
        date: '2025-01-01',
        overall_score: 3.0,
        dimension_scores: {
          requirements_analysis: 3.2,
          system_architecture: 2.8,
          technical_deep_dive: 3.0,
          scale_performance: 2.9,
          reliability_fault_tolerance: 3.1,
          communication_thought_process: 3.2
        }
      },
      {
        date: '2025-01-15',
        overall_score: 3.4,
        dimension_scores: {
          requirements_analysis: 3.6,
          system_architecture: 3.2,
          technical_deep_dive: 3.3,
          scale_performance: 3.1,
          reliability_fault_tolerance: 3.4,
          communication_thought_process: 3.8
        }
      },
      {
        date: '2025-02-01',
        overall_score: 3.8,
        dimension_scores: {
          requirements_analysis: 4.0,
          system_architecture: 3.8,
          technical_deep_dive: 3.6,
          scale_performance: 3.5,
          reliability_fault_tolerance: 3.7,
          communication_thought_process: 4.2
        }
      },
      {
        date: '2025-02-15',
        overall_score: 4.1,
        dimension_scores: {
          requirements_analysis: 4.2,
          system_architecture: 4.0,
          technical_deep_dive: 3.9,
          scale_performance: 3.8,
          reliability_fault_tolerance: 4.0,
          communication_thought_process: 4.5
        }
      }
    ]
  },
  trends: {
    overall_trend: 'improving',
    improving_dimensions: ['system_architecture', 'technical_deep_dive', 'communication_thought_process'],
    declining_dimensions: []
  },
  recommendations: [
    {
      description: 'Focus on database sharding strategies and consistency models',
      priority: 4,
      dimension: 'technical_deep_dive'
    },
    {
      description: 'Practice explaining CAP theorem trade-offs with concrete examples',
      priority: 4,
      dimension: 'communication_thought_process'
    },
    {
      description: 'Study load balancer algorithms and their use cases',
      priority: 3,
      dimension: 'scale_performance'
    },
    {
      description: 'Review circuit breaker patterns and failure handling',
      priority: 3,
      dimension: 'reliability_fault_tolerance'
    }
  ],
  goals: [
    {
      id: 'goal-1',
      description: 'Achieve 4.5+ overall score in system design assessments',
      target_date: '2025-12-31',
      status: 'active',
      progress: 75
    },
    {
      id: 'goal-2',
      description: 'Master distributed systems design patterns',
      target_date: '2025-06-30',
      status: 'active',
      progress: 40
    }
  ],
  achievements: [
    {
      name: 'First Assessment',
      description: 'Complete your first system design assessment',
      earned: true,
      date: '2025-01-01'
    },
    {
      name: 'Consistency Champion',
      description: 'Score 4.0+ in Technical Deep Dive dimension',
      earned: true,
      date: '2025-02-01'
    },
    {
      name: 'Communication Expert',
      description: 'Score 4.5+ in Communication dimension',
      earned: true,
      date: '2025-02-15'
    },
    {
      name: 'Architecture Guru',
      description: 'Score 4.5+ in System Architecture dimension',
      earned: false
    },
    {
      name: 'Scale Master',
      description: 'Design a system handling 1M+ users',
      earned: false
    },
    {
      name: 'Reliability Expert',
      description: 'Score 4.5+ in Reliability & Fault Tolerance dimension',
      earned: false
    }
  ],
  last_updated: '2025-08-14T10:00:00Z'
}

export default function ProgressPage() {
  const [progressData, setProgressData] = useState<ProgressData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const userId = 'john@example.com' // This would come from auth context

  useEffect(() => {
    loadProgressData()
  }, [])

  const loadProgressData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch(`/api/progress/${encodeURIComponent(userId)}`)
      
      if (!response.ok) {
        // Use mock data if API fails (for development)
        console.log('Using mock progress data for development')
        setProgressData(mockProgressData)
        return
      }

      const data = await response.json()
      setProgressData(data)
    } catch (err) {
      console.error('Failed to load progress data:', err)
      // Fallback to mock data
      setProgressData(mockProgressData)
    } finally {
      setIsLoading(false)
    }
  }

  const handleExportReport = async () => {
    try {
      const response = await fetch(`/api/progress/export/${encodeURIComponent(userId)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Export failed')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = `progress-report-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export report:', error)
      alert('Failed to export progress report. Please try again.')
    }
  }

  const handleSetGoal = async (goal: { description: string; target_date?: string }) => {
    try {
      const response = await fetch(`/api/progress/goals/${encodeURIComponent(userId)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(goal),
      })

      if (!response.ok) {
        throw new Error('Failed to set goal')
      }

      // Reload progress data to get updated goals
      loadProgressData()
    } catch (error) {
      console.error('Failed to set goal:', error)
      alert('Failed to set goal. Please try again.')
    }
  }

  const handleUpdateGoal = async (goalId: string, progress: number, status?: string) => {
    try {
      const response = await fetch(`/api/progress/goals/${goalId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ progress, status }),
      })

      if (!response.ok) {
        throw new Error('Failed to update goal')
      }

      // Reload progress data to get updated goals
      loadProgressData()
    } catch (error) {
      console.error('Failed to update goal:', error)
      alert('Failed to update goal. Please try again.')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center space-x-4 mb-8">
            <Link href="/chat">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Chat
              </Button>
            </Link>
          </div>
          
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading your progress data...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error && !progressData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center space-x-4 mb-8">
            <Link href="/chat">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Chat
              </Button>
            </Link>
          </div>
          
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-red-600 mb-4">Failed to load progress data</p>
              <Button onClick={loadProgressData} variant="outline">
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <Link href="/chat">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Chat
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Learning Progress</h1>
              <p className="text-gray-600 mt-1">
                Track your system design mastery over time
              </p>
            </div>
          </div>

          <Button onClick={handleExportReport} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>

        {/* Progress Dashboard */}
        {progressData && (
          <div className="bg-white rounded-lg shadow">
            <ProgressDashboard
              data={progressData}
              userId={userId}
              onExportReport={handleExportReport}
              onSetGoal={handleSetGoal}
              onUpdateGoal={handleUpdateGoal}
            />
          </div>
        )}
      </div>
    </div>
  )
}