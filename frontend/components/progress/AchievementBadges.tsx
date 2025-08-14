'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Trophy, Award, Star, Target, Calendar, CheckCircle, Lock } from 'lucide-react'
import { Achievement } from '../ProgressDashboard'

interface AchievementBadgesProps {
    achievements: Achievement[]
}

// Default achievements if none provided
const defaultAchievements: Achievement[] = [
    {
        name: 'First Assessment',
        description: 'Complete your first system design assessment',
        earned: false,
        icon: 'star'
    },
    {
        name: 'Consistent Learner',
        description: 'Complete assessments on 3 consecutive days',
        earned: false,
        icon: 'calendar'
    },
    {
        name: 'Architecture Expert',
        description: 'Score 4.5+ in System Architecture dimension',
        earned: false,
        icon: 'target'
    },
    {
        name: 'Well-Rounded',
        description: 'Score 4.0+ in all 6 dimensions in a single assessment',
        earned: false,
        icon: 'award'
    },
    {
        name: 'Communication Master',
        description: 'Score 4.8+ in Communication & Thought Process',
        earned: false,
        icon: 'trophy'
    },
    {
        name: 'Scale Specialist',
        description: 'Score 4.5+ in Scale & Performance dimension',
        earned: false,
        icon: 'target'
    },
    {
        name: 'Reliability Rock',
        description: 'Score 4.5+ in Reliability & Fault Tolerance',
        earned: false,
        icon: 'star'
    },
    {
        name: 'Rising Star',
        description: 'Improve overall score by 1.0 point within a week',
        earned: false,
        icon: 'star'
    },
    {
        name: 'Dedication',
        description: 'Complete 10 assessments',
        earned: false,
        icon: 'trophy'
    },
    {
        name: 'Perfect Score',
        description: 'Achieve a 5.0 overall score in any assessment',
        earned: false,
        icon: 'trophy'
    }
]

const getIcon = (iconName: string, earned: boolean) => {
    const iconClass = `h-6 w-6 ${earned ? 'text-yellow-600' : 'text-gray-400'}`
    
    switch (iconName) {
        case 'trophy':
            return <Trophy className={iconClass} />
        case 'award':
            return <Award className={iconClass} />
        case 'star':
            return <Star className={iconClass} />
        case 'target':
            return <Target className={iconClass} />
        case 'calendar':
            return <Calendar className={iconClass} />
        default:
            return <CheckCircle className={iconClass} />
    }
}

const getRarityColor = (name: string) => {
    const legendary = ['Perfect Score', 'Well-Rounded']
    const rare = ['Communication Master', 'Architecture Expert', 'Scale Specialist', 'Reliability Rock']
    const uncommon = ['Rising Star', 'Dedication', 'Consistent Learner']
    
    if (legendary.includes(name)) return 'border-purple-300 bg-purple-50'
    if (rare.includes(name)) return 'border-blue-300 bg-blue-50'
    if (uncommon.includes(name)) return 'border-green-300 bg-green-50'
    return 'border-gray-300 bg-gray-50'
}

const getRarityBadge = (name: string) => {
    const legendary = ['Perfect Score', 'Well-Rounded']
    const rare = ['Communication Master', 'Architecture Expert', 'Scale Specialist', 'Reliability Rock']
    const uncommon = ['Rising Star', 'Dedication', 'Consistent Learner']
    
    if (legendary.includes(name)) return <Badge className="bg-purple-100 text-purple-800">Legendary</Badge>
    if (rare.includes(name)) return <Badge className="bg-blue-100 text-blue-800">Rare</Badge>
    if (uncommon.includes(name)) return <Badge className="bg-green-100 text-green-800">Uncommon</Badge>
    return <Badge className="bg-gray-100 text-gray-800">Common</Badge>
}

export function AchievementBadges({ achievements }: AchievementBadgesProps) {
    const allAchievements = achievements.length > 0 ? achievements : defaultAchievements
    const earnedCount = allAchievements.filter(a => a.earned).length
    const totalCount = allAchievements.length
    const progressPercentage = (earnedCount / totalCount) * 100

    return (
        <div className="space-y-6">
            {/* Progress Overview */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Trophy className="h-5 w-5" />
                        Achievement Progress
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-lg font-semibold">
                                {earnedCount} of {totalCount} achievements earned
                            </span>
                            <Badge className="bg-yellow-100 text-yellow-800">
                                {Math.round(progressPercentage)}% Complete
                            </Badge>
                        </div>
                        
                        {/* Progress Bar */}
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                                className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${progressPercentage}%` }}
                            ></div>
                        </div>

                        <p className="text-sm text-gray-600">
                            Keep learning and practicing to unlock more achievements!
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Earned Achievements */}
            {earnedCount > 0 && (
                <div>
                    <h3 className="text-lg font-semibold mb-4 text-yellow-700 flex items-center gap-2">
                        <Trophy className="h-5 w-5" />
                        Earned Achievements ({earnedCount})
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {allAchievements
                            .filter(achievement => achievement.earned)
                            .map((achievement, index) => (
                                <Card 
                                    key={index} 
                                    className={`${getRarityColor(achievement.name)} border-2 transition-all duration-200 hover:scale-105`}
                                >
                                    <CardContent className="p-4">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                {getIcon(achievement.icon || 'star', true)}
                                                <div className="flex flex-col gap-1">
                                                    {getRarityBadge(achievement.name)}
                                                </div>
                                            </div>
                                            <CheckCircle className="h-4 w-4 text-green-600" />
                                        </div>
                                        
                                        <h4 className="font-semibold text-gray-900 mb-1">
                                            {achievement.name}
                                        </h4>
                                        <p className="text-sm text-gray-600 mb-2">
                                            {achievement.description}
                                        </p>
                                        
                                        {achievement.date && (
                                            <div className="text-xs text-gray-500 flex items-center gap-1">
                                                <Calendar className="h-3 w-3" />
                                                Earned {new Date(achievement.date).toLocaleDateString()}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            ))}
                    </div>
                </div>
            )}

            {/* Locked Achievements */}
            {earnedCount < totalCount && (
                <div>
                    <h3 className="text-lg font-semibold mb-4 text-gray-600 flex items-center gap-2">
                        <Lock className="h-5 w-5" />
                        Locked Achievements ({totalCount - earnedCount})
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {allAchievements
                            .filter(achievement => !achievement.earned)
                            .map((achievement, index) => (
                                <Card 
                                    key={index} 
                                    className="border border-gray-200 bg-gray-50 opacity-75 hover:opacity-90 transition-opacity"
                                >
                                    <CardContent className="p-4">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                {getIcon(achievement.icon || 'star', false)}
                                                <div className="flex flex-col gap-1">
                                                    {getRarityBadge(achievement.name)}
                                                </div>
                                            </div>
                                            <Lock className="h-4 w-4 text-gray-400" />
                                        </div>
                                        
                                        <h4 className="font-semibold text-gray-700 mb-1">
                                            {achievement.name}
                                        </h4>
                                        <p className="text-sm text-gray-500">
                                            {achievement.description}
                                        </p>
                                    </CardContent>
                                </Card>
                            ))}
                    </div>
                </div>
            )}

            {/* No Achievements State */}
            {earnedCount === 0 && achievements.length === 0 && (
                <Card>
                    <CardContent className="p-8">
                        <div className="text-center text-gray-500">
                            <Trophy className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p className="text-lg mb-2">No achievements yet</p>
                            <p className="text-sm">
                                Complete assessments and practice system design to start earning achievements!
                            </p>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}