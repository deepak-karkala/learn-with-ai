'use client'

import React, { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from "../components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { ScrollArea } from "../components/ui/scroll-area"
import { 
  BookOpen, 
  Play, 
  Pause,
  ArrowLeft,
  Clock,
  User,
  Star,
  FileText
} from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

interface LearningModule {
  id: string
  title: string
  description: string
  duration: string
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
  author: string
  rating: number
  hasText: boolean
}

interface LearnInterfaceProps {
  selectedModule?: string | null
  onModuleSelect: (moduleId: string | null) => void
}

const learningModules: LearningModule[] = [
  {
    id: 'api_design',
    title: 'API Design',
    description: 'Learn the fundamentals of API design, architectural styles, and best practices for building robust, scalable APIs.',
    duration: '45 min',
    difficulty: 'Intermediate',
    author: 'System Design Expert',
    rating: 4.8,
    hasText: true
  },
  {
    id: 'url_shortener',
    title: 'URL Shortener',
    description: 'Design a scalable URL shortening service like bit.ly, covering key system design concepts.',
    duration: '35 min',
    difficulty: 'Beginner',
    author: 'System Design Expert',
    rating: 4.7,
    hasText: true
  },
  {
    id: 'web_crawler',
    title: 'Web Crawler',
    description: 'Build a distributed web crawler system, exploring parallel processing and data storage strategies.',
    duration: '50 min',
    difficulty: 'Advanced',
    author: 'System Design Expert',
    rating: 4.9,
    hasText: true
  }
]

export function LearnInterface({ selectedModule, onModuleSelect }: LearnInterfaceProps) {
  const { theme } = useTheme()
  const [activeMode, setActiveMode] = useState<'text'>('text')
  const [moduleContent, setModuleContent] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [contentError, setContentError] = useState<string>('')

  const currentModule = selectedModule ? learningModules.find(m => m.id === selectedModule) : null

  useEffect(() => {
    if (selectedModule) {
      loadModuleContent(selectedModule)
    }
  }, [selectedModule, activeMode])

  const loadModuleContent = async (moduleId: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/content/${moduleId}/tutorial.md`)
      if (response.ok) {
        const data = await response.json()
        setModuleContent(data.content || 'Content not available.')
      } else {
        // Fallback to direct content loading for development
        try {
          const directResponse = await fetch(`/content/${moduleId}/tutorial.md`)
          if (directResponse.ok) {
            const content = await directResponse.text()
            setModuleContent(content)
          } else {
            console.error('Failed to load content:', directResponse.statusText)
            setModuleContent('Content not available.')
          }
        } catch (error) {
          console.error('Failed to load content:', error)
          setModuleContent('Content not available.')
        }
      }
    } catch (error) {
      console.error('Failed to load content:', error)
      setModuleContent('Content not available.')
    } finally {
      setIsLoading(false)
    }
  }

  const renderModuleList = () => (
    <div className="h-full flex flex-col">
      <div className="mb-6 flex-shrink-0">
        <h2 className={`text-xl font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
          Learning Modules
        </h2>
        <p className={`text-sm mt-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          Choose a module to start learning system design concepts
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="grid gap-3 pr-4">
          {learningModules.map((module) => (
            <Card 
              key={module.id}
              className={`cursor-pointer transition-all duration-200 hover:shadow-sm border rounded-lg ${
                theme === 'dark' 
                  ? 'bg-gray-800/50 border-gray-700/50 hover:border-gray-600 hover:bg-gray-800' 
                  : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
              onClick={() => onModuleSelect(module.id)}
            >
              <CardHeader className="pb-2 pt-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className={`text-base font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {module.title}
                    </CardTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge 
                        variant={module.difficulty === 'Beginner' ? 'default' : 
                                 module.difficulty === 'Intermediate' ? 'secondary' : 'destructive'}
                        className="text-xs"
                      >
                        {module.difficulty}
                      </Badge>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-gray-500" />
                        <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                          {module.duration}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 text-yellow-400 fill-current" />
                        <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                          {module.rating}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 pb-4">
                <p className={`text-sm mb-3 line-clamp-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                  {module.description}
                </p>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3 text-gray-500" />
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                      {module.author}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    {module.hasText && <FileText className="h-4 w-4 text-blue-500" />}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  )

  const renderModuleContent = () => {
    if (!currentModule) return null

    return (
      <div className="space-y-4">
        {/* Module Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onModuleSelect(null)}
            className={`p-2 ${theme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className={`text-xl font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              {currentModule.title}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="secondary" className="text-xs">
                {currentModule.difficulty}
              </Badge>
              <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                {currentModule.duration}
              </span>
            </div>
          </div>
        </div>

        {/* Learning Mode Tabs */}
        <div className="flex gap-2 mb-6">
          <Button
            variant={activeMode === 'text' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveMode('text')}
            className="flex items-center gap-2"
            disabled={!currentModule.hasText}
          >
            <BookOpen className="h-4 w-4" />
            Notes
          </Button>
        </div>

        {/* Content Area */}
        <Card className={`border rounded-lg ${theme === 'dark' ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}`}>
          <CardContent className="p-6">
            {activeMode === 'text' && (
              <ScrollArea className="h-96">
                {isLoading ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : (
                  <div className={`prose ${theme === 'dark' ? 'prose-invert' : ''} max-w-none prose-sm text-sm leading-relaxed`}>
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({...props}) => <h1 className="text-xl font-semibold mt-6 mb-3 first:mt-0" {...props} />,
                        h2: ({...props}) => <h2 className="text-lg font-medium mt-5 mb-2" {...props} />,
                        h3: ({...props}) => <h3 className="text-base font-medium mt-4 mb-2" {...props} />,
                        h4: ({...props}) => <h4 className="text-sm font-medium mt-3 mb-1" {...props} />,
                        p: ({...props}) => <p className="mb-4 leading-relaxed" {...props} />,
                        ul: ({...props}) => <ul className="mb-4 ml-6 list-disc space-y-1" {...props} />,
                        ol: ({...props}) => <ol className="mb-4 ml-6 list-decimal space-y-1" {...props} />,
                        li: ({...props}) => <li className="leading-relaxed" {...props} />,
                        blockquote: ({...props}) => (
                          <blockquote 
                            className={`border-l-4 pl-4 my-4 italic ${
                              theme === 'dark' ? 'border-gray-600 text-gray-300' : 'border-gray-300 text-gray-600'
                            }`} 
                            {...props} 
                          />
                        ),
                        code: ({children, ...props}) => (
                          <code 
                            className={`px-1 py-0.5 rounded text-sm font-mono ${
                              theme === 'dark' ? 'bg-gray-700 text-gray-200' : 'bg-gray-100 text-gray-800'
                            }`} 
                            {...props}
                          >
                            {children}
                          </code>
                        ),
                        pre: ({children, ...props}) => (
                          <pre 
                            className={`mb-4 p-3 rounded-lg overflow-x-auto ${
                              theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'
                            }`} 
                            {...props} 
                          >
                            {children}
                          </pre>
                        ),
                        table: ({...props}) => (
                          <div className="overflow-x-auto mb-4">
                            <table 
                              className={`min-w-full border-collapse border ${
                                theme === 'dark' ? 'border-gray-600' : 'border-gray-300'
                              }`} 
                              {...props} 
                            />
                          </div>
                        ),
                        th: ({...props}) => (
                          <th 
                            className={`border px-3 py-2 text-left font-semibold ${
                              theme === 'dark' ? 'border-gray-600 bg-gray-700' : 'border-gray-300 bg-gray-100'
                            }`} 
                            {...props} 
                          />
                        ),
                        td: ({...props}) => (
                          <td 
                            className={`border px-3 py-2 ${
                              theme === 'dark' ? 'border-gray-600' : 'border-gray-300'
                            }`} 
                            {...props} 
                          />
                        ),
                        strong: ({...props}) => <strong className="font-semibold" {...props} />,
                        em: ({...props}) => <em className="italic" {...props} />,
                        a: ({...props}) => (
                          <a 
                            className={`underline hover:no-underline ${
                              theme === 'dark' ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'
                            }`} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            {...props} 
                          />
                        ),
                      }}
                    >
                      {moduleContent}
                    </ReactMarkdown>
                  </div>
                )}
              </ScrollArea>
            )}

          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="h-full p-6">
      {selectedModule ? renderModuleContent() : renderModuleList()}
    </div>
  )
}
