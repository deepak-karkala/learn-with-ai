'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from "../components/ui/button"
import { Slider } from "../components/ui/slider"
import { Card, CardContent } from "../components/ui/card"
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  SkipBack,
  SkipForward,
  RotateCcw,
  Music,
  Headphones
} from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

interface AudioPlayerProps {
  src: string
  title: string
  className?: string
  onError?: (error: string) => void
}

export function AudioPlayer({ src, title, className = '', onError }: AudioPlayerProps) {
  const { theme } = useTheme()
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime)
    const handleDurationChange = () => setDuration(audio.duration)
    const handleLoadedData = () => setIsLoading(false)
    const handleError = () => {
      setHasError(true)
      setIsLoading(false)
      onError?.('Failed to load audio. Please check if the audio file exists.')
    }
    const handleEnded = () => setIsPlaying(false)

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('durationchange', handleDurationChange)
    audio.addEventListener('loadeddata', handleLoadedData)
    audio.addEventListener('error', handleError)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('durationchange', handleDurationChange)
      audio.removeEventListener('loadeddata', handleLoadedData)
      audio.removeEventListener('error', handleError)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [onError])

  const togglePlay = () => {
    if (!audioRef.current) return
    
    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleSeek = (value: number[]) => {
    if (!audioRef.current) return
    const time = (value[0] / 100) * duration
    audioRef.current.currentTime = time
    setCurrentTime(time)
  }

  const handleVolumeChange = (value: number[]) => {
    if (!audioRef.current) return
    const newVolume = value[0] / 100
    audioRef.current.volume = newVolume
    setVolume(newVolume)
    setIsMuted(newVolume === 0)
  }

  const toggleMute = () => {
    if (!audioRef.current) return
    if (isMuted) {
      audioRef.current.volume = volume
      setIsMuted(false)
    } else {
      audioRef.current.volume = 0
      setIsMuted(true)
    }
  }

  const skipBackward = () => {
    if (!audioRef.current) return
    audioRef.current.currentTime = Math.max(0, currentTime - 10)
  }

  const skipForward = () => {
    if (!audioRef.current) return
    audioRef.current.currentTime = Math.min(duration, currentTime + 10)
  }

  const restart = () => {
    if (!audioRef.current) return
    audioRef.current.currentTime = 0
    setCurrentTime(0)
  }

  const changePlaybackRate = () => {
    if (!audioRef.current) return
    const rates = [0.5, 0.75, 1, 1.25, 1.5, 2]
    const currentIndex = rates.indexOf(playbackRate)
    const nextRate = rates[(currentIndex + 1) % rates.length]
    audioRef.current.playbackRate = nextRate
    setPlaybackRate(nextRate)
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  if (hasError) {
    return (
      <Card className={`${className} ${
        theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center text-center">
            <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
              theme === 'dark' ? 'bg-gray-700' : 'bg-gray-100'
            }`}>
              <Headphones className={`w-8 h-8 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`} />
            </div>
            <h3 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Audio Not Available
            </h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              The audio file for {title} is not yet available.
            </p>
            <p className={`text-xs mt-2 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
              Audio content will be added soon.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={`${className} ${
      theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
    }`}>
      <audio ref={audioRef} src={src} />
      
      <CardContent className="p-6">
        {/* Header with Audio Icon and Title */}
        <div className="flex items-center space-x-3 mb-6">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
            isPlaying 
              ? 'bg-blue-500 text-white' 
              : theme === 'dark' ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'
          }`}>
            <Music className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <h3 className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              {title}
            </h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              System Design Audio Lesson
            </p>
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!isLoading && (
          <>
            {/* Progress Bar */}
            <div className="mb-4">
              <Slider
                value={[duration ? (currentTime / duration) * 100 : 0]}
                onValueChange={handleSeek}
                max={100}
                step={0.1}
                className="w-full"
              />
              <div className={`flex justify-between text-xs mt-2 ${
                theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            {/* Main Controls */}
            <div className="flex items-center justify-center space-x-4 mb-4">
              <Button
                onClick={restart}
                size="sm"
                variant="outline"
                className={`${
                  theme === 'dark' ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : ''
                }`}
              >
                <RotateCcw className="w-4 h-4" />
              </Button>

              <Button
                onClick={skipBackward}
                size="sm"
                variant="outline"
                className={`${
                  theme === 'dark' ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : ''
                }`}
              >
                <SkipBack className="w-4 h-4" />
              </Button>

              <Button
                onClick={togglePlay}
                size="lg"
                className="w-14 h-14 rounded-full"
              >
                {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
              </Button>

              <Button
                onClick={skipForward}
                size="sm"
                variant="outline"
                className={`${
                  theme === 'dark' ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : ''
                }`}
              >
                <SkipForward className="w-4 h-4" />
              </Button>

              <Button
                onClick={changePlaybackRate}
                size="sm"
                variant="outline"
                className={`px-3 ${
                  theme === 'dark' ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : ''
                }`}
              >
                {playbackRate}x
              </Button>
            </div>

            {/* Volume Controls */}
            <div className="flex items-center justify-center space-x-3">
              <Button
                onClick={toggleMute}
                size="sm"
                variant="ghost"
                className={`${
                  theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : ''
                }`}
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </Button>
              
              <div className="flex-1 max-w-32">
                <Slider
                  value={[isMuted ? 0 : volume * 100]}
                  onValueChange={handleVolumeChange}
                  max={100}
                  step={1}
                />
              </div>
              
              <span className={`text-xs w-8 text-center ${
                theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {Math.round(isMuted ? 0 : volume * 100)}%
              </span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}