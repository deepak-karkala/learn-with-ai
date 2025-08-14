'use client'

import React, { useState } from 'react'
import { ChapterSelection } from '@/components/ChapterSelection'

export default function ChaptersPage() {
  const [selectedChapter, setSelectedChapter] = useState<string>()

  const handleChapterSelect = (chapterId: string) => {
    setSelectedChapter(chapterId)
    
    // Store the selected chapter in localStorage for the chat interface
    localStorage.setItem('selectedChapter', chapterId)
    
    // Navigate to chat after a brief delay to show selection feedback
    setTimeout(() => {
      window.location.href = '/chat'
    }, 1000)
  }

  return (
    <ChapterSelection 
      onChapterSelect={handleChapterSelect}
      selectedChapter={selectedChapter}
    />
  )
}