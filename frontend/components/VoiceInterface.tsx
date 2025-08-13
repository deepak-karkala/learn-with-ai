'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Mic, Square } from 'lucide-react'

interface VoiceInterfaceProps {
  /**
   * When true, renders a compact inline button suitable for toolbars
   * (e.g. next to the chat send button). Status text and level meter are
   * hidden, but audio playback still functions.
   */
  inline?: boolean
}

export function VoiceInterface({ inline = false }: VoiceInterfaceProps) {
  const [status, setStatus] = useState<'idle' | 'recording' | 'processing'>('idle')
  const [permissionError, setPermissionError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const socketRef = useRef<WebSocket | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const [level, setLevel] = useState(0)

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      audioContextRef.current = new AudioCtx()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      source.connect(analyserRef.current)

      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder

      const wsUrl = process.env.NEXT_PUBLIC_VOICE_WS_URL || 'ws://localhost:8000/api/voice'
      const socket = new WebSocket(wsUrl)
      socket.binaryType = 'arraybuffer'
      socketRef.current = socket

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0 && socket.readyState === WebSocket.OPEN) {
          socket.send(e.data)
        }
      }

      socket.onmessage = (event: MessageEvent<ArrayBuffer>) => {
        const blob = new Blob([event.data], { type: 'audio/webm' })
        const url = URL.createObjectURL(blob)
        if (audioRef.current) {
          audioRef.current.src = url
          audioRef.current.play().catch(() => {})
        }
      }

      mediaRecorder.start(250)
      setStatus('recording')
      setPermissionError(null)
    } catch (err) {
      setPermissionError('Microphone access denied')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    socketRef.current?.close()
    setStatus('processing')
    setTimeout(() => setStatus('idle'), 500)
  }

  const handleRecord = () => {
    if (status === 'idle') {
      startRecording()
    } else if (status === 'recording') {
      stopRecording()
    }
  }

  useEffect(() => {
    let raf: number
    const updateLevel = () => {
      if (analyserRef.current) {
        const array = new Uint8Array(analyserRef.current.fftSize)
        analyserRef.current.getByteTimeDomainData(array)
        let max = 0
        for (let i = 0; i < array.length; i++) {
          const val = Math.abs(array[i] - 128) / 128
          if (val > max) max = val
        }
        setLevel(max)
      }
      raf = requestAnimationFrame(updateLevel)
    }
    if (status === 'recording') {
      raf = requestAnimationFrame(updateLevel)
    } else {
      cancelAnimationFrame(raf)
      setLevel(0)
    }
    return () => cancelAnimationFrame(raf)
  }, [status])

  return (
    <div className={inline ? 'flex items-center' : 'flex flex-col items-center gap-2'}>
      <Button
        data-testid="record-button"
        onClick={handleRecord}
        size={inline ? 'icon' : undefined}
        aria-label={status === 'recording' ? 'Stop recording' : 'Start recording'}
      >
        {status === 'recording'
          ? inline
            ? <Square className="h-4 w-4" />
            : 'Stop'
          : inline
            ? <Mic className="h-4 w-4" />
            : 'Record'}
      </Button>
      {!inline && status === 'recording' && <div>Recording...</div>}
      {!inline && status === 'processing' && <div>Processing...</div>}
      {!inline && permissionError && <div className="text-red-500">{permissionError}</div>}
      {!inline && (
        <div className="h-2 w-32 bg-gray-200" aria-label="voice-level">
          <div
            className="h-2 bg-green-500"
            style={{ width: `${Math.min(level * 100, 100)}%` }}
            data-testid="vad-bar"
          />
        </div>
      )}
      <audio ref={audioRef} data-testid="playback" />
    </div>
  )
}

export default VoiceInterface
