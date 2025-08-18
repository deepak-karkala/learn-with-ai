'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { 
  MessageSquare, 
  BarChart3, 
  User, 
  Settings, 
  CreditCard,
  Plus,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  BookOpen,
  GraduationCap,
  Star
} from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'

interface Session {
  id: string
  title: string
  created_at: string
  message_count: number
}

interface LearningModule {
  id: string
  title: string
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
  rating: number
  completed?: boolean
}

interface SidebarProps {
  sessions: Session[]
  currentSessionId?: string
  mainSessionId?: string
  onNewSession: () => void
  onSelectSession: (sessionId: string) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  onModuleSelect?: (moduleId: string) => void
  selectedModule?: string | null
}

export function Sidebar({ 
  sessions, 
  currentSessionId, 
  mainSessionId,
  onNewSession, 
  onSelectSession,
  isCollapsed = false,
  onToggleCollapse,
  onModuleSelect,
  selectedModule
}: SidebarProps) {
  const { theme, toggleTheme } = useTheme()
  const [userStats] = useState({
    name: 'John Doe',
    email: 'john@example.com',
    totalSessions: sessions.length,
    currentScore: 3.8,
    subscription: 'Pro'
  })

  const learningModules: LearningModule[] = [
    {
      id: 'api_design',
      title: 'API Design',
      difficulty: 'Intermediate',
      rating: 4.8,
      completed: false
    },
    {
      id: 'url_shortener',
      title: 'URL Shortener',
      difficulty: 'Beginner',
      rating: 4.7,
      completed: false
    },
    {
      id: 'web_crawler',
      title: 'Web Crawler',
      difficulty: 'Advanced',
      rating: 4.9,
      completed: false
    }
  ]

  return (
    <div className={`${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50 border-r border-gray-200'} flex flex-col transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-56'
    }`}>
      {/* Header */}
      <div className={`p-3 border-b ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
        {!isCollapsed ? (
          <div className="flex flex-col space-y-3">
            {/* Logo and Controls Row */}
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 flex items-center justify-center">
                <img 
                  src={theme === 'dark' ? "/logo-dark.png" : "/logo.png"} 
                  alt="Learn System Design with AI" 
                  className="w-10 h-10 object-contain"
                />
              </div>
              <div className="flex items-center gap-1">
                {/* Theme Toggle */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleTheme}
                  className={`p-1 h-6 w-6 rounded-lg ${
                    theme === 'dark' 
                      ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                >
                  {theme === 'dark' ? <Sun className="h-3 w-3" /> : <Moon className="h-3 w-3" />}
                </Button>
                {onToggleCollapse && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onToggleCollapse}
                    className={`p-1 h-6 w-6 rounded-lg ${
                      theme === 'dark' 
                        ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <ChevronLeft className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>
            {/* Title Row - Centered */}
            <div className="text-center">
              <h1 className={`text-lg font-bold tracking-tight leading-tight ${
                theme === 'dark' ? 'text-white' : 'text-gray-900'
              }`} style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
                Learn System Design
                <br />
                <span className="text-blue-600 font-extrabold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">with AI</span>
              </h1>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 flex items-center justify-center">
              <img 
                src={theme === 'dark' ? "/logo-dark.png" : "/logo.png"} 
                alt="Learn System Design with AI" 
                className="w-8 h-8 object-contain"
              />
            </div>
            <div className="flex items-center gap-1">
              {/* Theme Toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleTheme}
                className={`p-1 h-6 w-6 rounded-lg ${
                  theme === 'dark' 
                    ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              >
                {theme === 'dark' ? <Sun className="h-3 w-3" /> : <Moon className="h-3 w-3" />}
              </Button>
              {onToggleCollapse && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onToggleCollapse}
                  className={`p-1 h-6 w-6 rounded-lg ${
                    theme === 'dark' 
                      ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <ChevronRight className="h-3 w-3" />
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* New Session Button */}
      <div className="p-3">
        <Button 
          onClick={onNewSession}
          className={`w-full justify-start ${isCollapsed ? 'px-2' : ''} transition-all duration-200 rounded-xl ${
            theme === 'dark' 
              ? 'bg-white/10 hover:bg-white/20 border-gray-700 text-gray-200 hover:text-white'
              : 'bg-white hover:bg-gray-100 border-gray-300 text-gray-700 hover:text-gray-900 shadow-sm'
          }`}
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          {!isCollapsed && <span className="ml-2">New Session</span>}
        </Button>
      </div>

      {/* Sessions List */}
      {!isCollapsed && (
        <div className="flex-1 px-3">
          <div className="mb-3">
            <span className={`text-xs font-medium uppercase tracking-wide ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Recent Sessions
            </span>
          </div>
          <ScrollArea className="h-40">
            {sessions.length > 0 ? (
              <div className="space-y-2">
                {sessions.slice(0, 10).map((session) => (
                  <button
                    key={session.id}
                    onClick={() => onSelectSession(session.id)}
                    className={`w-full text-left p-1.5 rounded-lg text-sm transition-all duration-200 ${
                      (currentSessionId === session.id || 
                       (session.id.startsWith('current_session_') && currentSessionId === mainSessionId))
                        ? (theme === 'dark' 
                            ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                            : 'bg-blue-100 text-blue-900 border border-blue-200'
                          )
                        : (theme === 'dark' 
                            ? 'hover:bg-gray-800 text-gray-300 hover:text-white'
                            : 'hover:bg-gray-100 text-gray-700 hover:text-gray-900'
                          )
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">
                          {session.title || 'Untitled Session'}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className={`text-center py-8 text-sm ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
                No sessions yet
              </div>
            )}
          </ScrollArea>
        </div>
      )}

      {/* Learning Modules Section */}
      {!isCollapsed && onModuleSelect && (
        <div className="px-3 min-h-0 flex-1">
          <div className="mb-2">
            <span className={`text-xs font-medium uppercase tracking-wide ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Learning Modules
            </span>
          </div>
          <ScrollArea className="h-32">
            {learningModules.length > 0 ? (
              <div className="space-y-1 pr-2">
                {learningModules.map((module) => (
                  <button
                    key={module.id}
                    onClick={() => onModuleSelect(module.id)}
                    className={`w-full text-left p-1.5 rounded-lg text-sm transition-all duration-200 ${
                      selectedModule === module.id
                        ? (theme === 'dark' 
                            ? 'bg-green-600/20 text-green-300 border border-green-500/30'
                            : 'bg-green-100 text-green-900 border border-green-200'
                          )
                        : (theme === 'dark' 
                            ? 'hover:bg-gray-800 text-gray-300 hover:text-white'
                            : 'hover:bg-gray-100 text-gray-700 hover:text-gray-900'
                          )
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <BookOpen className="h-3 w-3 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium truncate">
                            {module.title}
                          </p>
                        </div>
                      </div>
                      {module.completed && (
                        <div className="w-2 h-2 bg-green-400 rounded-full ml-1"></div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className={`text-center py-4 text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
                No modules available
              </div>
            )}
          </ScrollArea>
        </div>
      )}

      <div className={`border-t my-1 ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}></div>

      {/* Navigation Links */}
      <div className="p-3">
        <Link href="/progress">
          <Button 
            variant="ghost" 
            className={`w-full justify-start ${isCollapsed ? 'px-2' : ''} rounded-xl transition-all duration-200 ${
              theme === 'dark' 
                ? 'text-gray-300 hover:text-white hover:bg-gray-800'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            {!isCollapsed && <span className="ml-2">Progress</span>}
          </Button>
        </Link>
      </div>

      <div className={`border-t my-1 ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}></div>

      {/* User Profile Section */}
      <div className="p-3">
        {!isCollapsed ? (
          <div className="flex items-center space-x-3">
            <Avatar className="h-8 w-8 ring-2 ring-gray-700">
              <AvatarImage src="/api/placeholder/32/32" alt={userStats.name} />
              <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">{userStats.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className={`text-sm font-medium truncate ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {userStats.name}
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="default" className="text-xs bg-gradient-to-r from-blue-500 to-purple-600 text-white">
                    {userStats.subscription}
                  </Badge>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    className={`p-1 h-6 w-6 rounded-lg ${
                      theme === 'dark' 
                        ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                    title="Settings"
                  >
                    <Settings className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2">
            <Avatar className={`h-8 w-8 ring-2 ${theme === 'dark' ? 'ring-gray-700' : 'ring-gray-300'}`}>
              <AvatarImage src="/api/placeholder/32/32" alt={userStats.name} />
              <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">{userStats.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <Badge variant="default" className="text-xs bg-gradient-to-r from-blue-500 to-purple-600 text-white">
              {userStats.subscription}
            </Badge>
          </div>
        )}
      </div>
    </div>
  )
}