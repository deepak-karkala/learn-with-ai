import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { VoiceInterface } from '../components/VoiceInterface'

class MockMediaRecorder {
  public ondataavailable: ((e: any) => void) | null = null
  constructor(_stream: MediaStream) {}
  start() {
    setTimeout(() => {
      this.ondataavailable && this.ondataavailable({ data: new Blob(['audio']) })
    }, 0)
  }
  stop() {}
}

class MockWebSocket {
  readyState = 1
  onmessage: ((ev: any) => void) | null = null
  send = jest.fn()
  close = jest.fn()
  constructor(_url: string) {}
}

HTMLMediaElement.prototype.play = jest.fn().mockResolvedValue(undefined)
;(global as any).URL = { createObjectURL: jest.fn(() => 'blob:mock') }
;(global as any).MediaStream = class {}
;(global as any).AudioContext = class {
  createMediaStreamSource() { return { connect: jest.fn() } }
  createAnalyser() { return { fftSize: 32, getByteTimeDomainData: jest.fn() } }
}
;(global as any).navigator.mediaDevices = {
  getUserMedia: jest.fn().mockResolvedValue(new MediaStream()),
}

describe('VoiceInterface integration', () => {
  it('plays audio from websocket', async () => {
    const wsInstance = new MockWebSocket('')
    ;(global as any).WebSocket = jest.fn(() => wsInstance)
    global.MediaRecorder = MockMediaRecorder as any

    render(<VoiceInterface />)
    const button = screen.getByTestId('record-button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('Recording...')).toBeInTheDocument()
    })

    const buffer = new ArrayBuffer(8)
    wsInstance.onmessage && wsInstance.onmessage({ data: buffer })

    await waitFor(() => {
      const audio = screen.getByTestId('playback') as HTMLAudioElement
      expect(audio.src).toContain('blob:')
      expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()
    })
  })
})
