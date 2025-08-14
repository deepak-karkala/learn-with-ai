import { render, screen } from './test-utils'
import Home from '../app/page'

describe('Home', () => {
  it('renders the main heading', () => {
    render(<Home />)

    const heading = screen.getByText('AI System Design Learning Platform')

    expect(heading).toBeInTheDocument()
  })

  it('renders all feature cards', () => {
    render(<Home />)

    expect(screen.getByText('Interactive Learning')).toBeInTheDocument()
    expect(screen.getByText('Real-time Feedback')).toBeInTheDocument()
    expect(screen.getByText('Progress Tracking')).toBeInTheDocument()
    expect(screen.getByText('AI Diagrams')).toBeInTheDocument()
  })
})