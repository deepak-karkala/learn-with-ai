import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { VoiceInterface } from '../components/VoiceInterface'

class MockMediaRecorder {
  public ondataavailable: ((e: any) => void) | null = null
  public onstop: (() => void) | null = null
  constructor(_stream: MediaStream) {}
  start() {
    setTimeout(() => {
      this.ondataavailable && this.ondataavailable({ data: new Blob(['audio']) })
    }, 0)
  }
  stop() {
    this.onstop && this.onstop()
  }
}

class MockWebSocket {
  readyState = 1
  onmessage: ((ev: any) => void) | null = null
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: ((err: any) => void) | null = null
  send = jest.fn()
  close = jest.fn()
  constructor(_url: string) {
    // Simulate WebSocket opening after a short delay
    setTimeout(() => {
      if (this.onopen) {
        this.onopen()
      }
    }, 10)
  }
}

HTMLMediaElement.prototype.play = jest.fn().mockResolvedValue(undefined)
;(global as any).URL = { createObjectURL: jest.fn(() => 'blob:mock') }
;(global as any).MediaStream = class {}
;(global as any).AudioContext = class {
  destination = {}
  createMediaStreamSource() { return { connect: jest.fn() } }
  createAnalyser() { return { fftSize: 32, getByteTimeDomainData: jest.fn() } }
  createScriptProcessor() { 
    return { 
      connect: jest.fn(), 
      disconnect: jest.fn(),
      onaudioprocess: null 
    } 
  }
  close() { return Promise.resolve() }
}
;(global as any).navigator.mediaDevices = {
  getUserMedia: jest.fn().mockResolvedValue(new MediaStream()),
}

describe('VoiceInterface integration', () => {
  it('processes audio from websocket through queue system', async () => {
    const wsInstance = new MockWebSocket('')
    ;(global as any).WebSocket = jest.fn(() => wsInstance)
    global.MediaRecorder = MockMediaRecorder as any

    // Mock console.log to capture audio queue logs
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()

    render(<VoiceInterface />)
    const button = screen.getByTestId('record-button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('Recording...')).toBeInTheDocument()
    })

    // Send JSON message as per Gemini Live API requirements
    const mockAudioMessage = {
      mime_type: "audio/pcm",
      data: btoa("mock audio data") // Base64 encoded mock audio
    }
    wsInstance.onmessage && wsInstance.onmessage({ data: JSON.stringify(mockAudioMessage) })

    // Wait for audio queue processing
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('[AUDIO QUEUE]: Processing'))
    }, { timeout: 1000 })

    consoleSpy.mockRestore()
  })
})
