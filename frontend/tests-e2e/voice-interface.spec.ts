import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async () => new MediaStream()
    // @ts-ignore
    window.MediaRecorder = class {
      ondataavailable: (e: any) => void = () => {}
      start() {
        setTimeout(() => this.ondataavailable({ data: new Blob(['audio']) }), 0)
      }
      stop() {}
    }
  })
})

test('voice recording starts and stops', async ({ page }) => {
  await page.goto('/chat')
  const recordButton = page.getByTestId('record-button')
  await recordButton.click()
  await expect(page.getByText('Recording...')).toBeVisible()
  await recordButton.click()
  await expect(page.getByText('Processing...')).toBeVisible()
})
