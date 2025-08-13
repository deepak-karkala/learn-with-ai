import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { VoiceInterface } from '../components/VoiceInterface'

// Simple mocks for browser APIs
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

global.MediaRecorder = MockMediaRecorder as any
;(global as any).WebSocket = MockWebSocket
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

HTMLMediaElement.prototype.play = jest.fn().mockResolvedValue(undefined)

describe('VoiceInterface', () => {
  it('voice recording starts and stops', async () => {
    const wsInstance = new MockWebSocket('')
    ;(global as any).WebSocket = jest.fn(() => wsInstance)

    render(<VoiceInterface />)
    const button = screen.getByTestId('record-button')

    fireEvent.click(button)
    await waitFor(() => {
      expect(screen.getByText('Recording...')).toBeInTheDocument()
    })

    fireEvent.click(button)
    await waitFor(() => {
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })
  })
})
