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
  Moon
} from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'

interface Session {
  id: string
  title: string
  created_at: string
  message_count: number
}

interface SidebarProps {
  sessions: Session[]
  currentSessionId?: string
  onNewSession: () => void
  onSelectSession: (sessionId: string) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export function Sidebar({ 
  sessions, 
  currentSessionId, 
  onNewSession, 
  onSelectSession,
  isCollapsed = false,
  onToggleCollapse
}: SidebarProps) {
  const { theme, toggleTheme } = useTheme()
  const [userStats] = useState({
    name: 'John Doe',
    email: 'john@example.com',
    totalSessions: sessions.length,
    currentScore: 3.8,
    subscription: 'Pro'
  })

  return (
    <div className={`${theme === 'dark' ? 'bg-gray-900' : 'bg-white border-r border-gray-200'} flex flex-col transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-56'
    }`}>
      {/* Header */}
      <div className={`p-4 border-b ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-sm">SD</span>
              </div>
              <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>System Design</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className={`p-1 h-8 w-8 rounded-lg ${
                theme === 'dark' 
                  ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            {onToggleCollapse && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleCollapse}
                className={`p-1 h-8 w-8 rounded-lg ${
                  theme === 'dark' 
                    ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* New Session Button */}
      <div className="p-4">
        <Button 
          onClick={onNewSession}
          className={`w-full justify-start ${isCollapsed ? 'px-2' : ''} transition-all duration-200 rounded-xl ${
            theme === 'dark' 
              ? 'bg-white/10 hover:bg-white/20 border-gray-700 text-gray-200 hover:text-white'
              : 'bg-gray-100 hover:bg-gray-200 border-gray-300 text-gray-700 hover:text-gray-900'
          }`}
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          {!isCollapsed && <span className="ml-2">New Session</span>}
        </Button>
      </div>

      {/* Sessions List */}
      {!isCollapsed && (
        <div className="flex-1 px-4">
          <div className="mb-3">
            <span className={`text-xs font-medium uppercase tracking-wider ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Recent Sessions
            </span>
          </div>
          <ScrollArea className="h-64">
            {sessions.length > 0 ? (
              <div className="space-y-2">
                {sessions.slice(0, 10).map((session) => (
                  <button
                    key={session.id}
                    onClick={() => onSelectSession(session.id)}
                    className={`w-full text-left p-2.5 rounded-lg text-sm transition-all duration-200 ${
                      currentSessionId === session.id
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
                        <p className="font-medium truncate text-sm">
                          {session.title || 'Untitled Session'}
                        </p>
                        <p className={`text-xs mt-0.5 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
                          {new Date(session.created_at).toLocaleDateString()}
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

      <div className={`border-t my-2 ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}></div>

      {/* Navigation Links */}
      <div className="p-4 space-y-2">
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

        <Button 
          variant="ghost" 
          className={`w-full justify-start ${isCollapsed ? 'px-2' : ''} rounded-xl transition-all duration-200 ${
            theme === 'dark' 
              ? 'text-gray-300 hover:text-white hover:bg-gray-800'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <Settings className="h-4 w-4" />
          {!isCollapsed && <span className="ml-2">Settings</span>}
        </Button>
      </div>

      <div className={`border-t my-2 ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}></div>

      {/* User Profile Section */}
      <div className="p-4">
        {!isCollapsed ? (
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <Avatar className="h-8 w-8 ring-2 ring-gray-700">
                <AvatarImage src="/api/placeholder/32/32" alt={userStats.name} />
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">{userStats.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium truncate ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {userStats.name}
                </p>
                <p className={`text-xs truncate ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  {userStats.email}
                </p>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className={`p-3 rounded-xl border ${
                theme === 'dark' 
                  ? 'bg-gray-800 border-gray-700' 
                  : 'bg-gray-50 border-gray-200'
              }`}>
                <div className={`font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>Score</div>
                <div className="text-blue-400 font-semibold text-lg">{userStats.currentScore}/5.0</div>
              </div>
              <div className={`p-3 rounded-xl border ${
                theme === 'dark' 
                  ? 'bg-gray-800 border-gray-700' 
                  : 'bg-gray-50 border-gray-200'
              }`}>
                <div className={`font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>Sessions</div>
                <div className="text-green-400 font-semibold text-lg">{userStats.totalSessions}</div>
              </div>
            </div>

            {/* Subscription Status */}
            <div className="flex items-center justify-between">
              <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>Plan</span>
              <Badge variant="default" className="text-xs bg-gradient-to-r from-blue-500 to-purple-600 text-white">
                {userStats.subscription}
              </Badge>
            </div>

            <Button variant="outline" size="sm" className={`w-full rounded-xl transition-all duration-200 ${
              theme === 'dark' 
                ? 'bg-white/5 hover:bg-white/10 border-gray-700 text-gray-300 hover:text-white'
                : 'bg-gray-100 hover:bg-gray-200 border-gray-300 text-gray-700 hover:text-gray-900'
            }`}>
              <CreditCard className="h-3 w-3 mr-2" />
              Manage Plan
            </Button>
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