import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-8 space-y-8">
      <div className="z-10 max-w-6xl w-full items-center justify-center text-center">
        <h1 className="text-4xl font-bold mb-4">
          AI System Design Learning Platform
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Interactive AI-powered platform for learning system design
        </p>
        <div className="mb-8">
          <Link
            href="/chat"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
            data-testid="start-learning"
          >
            🚀 Start Learning Now
          </Link>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="grid text-center lg:max-w-5xl lg:w-full lg:grid-cols-4 lg:text-left gap-4">
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            Interactive Learning{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Learn system design through AI-powered conversations and interactive whiteboarding.
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            Real-time Feedback{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Get instant analysis and feedback on your architecture diagrams.
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            Progress Tracking{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Track your learning progress with 6-dimensional assessments.
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            AI Diagrams{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Generate architecture diagrams from conversation context.
          </p>
        </div>
      </div>

      {/* Quick Start Section */}
      <div className="w-full max-w-4xl text-center">
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h2 className="text-2xl font-semibold text-blue-900 mb-4">
            Ready to Start Learning?
          </h2>
          <p className="text-blue-700 mb-6">
            Jump into interactive conversations with our AI assistant and start mastering system design concepts today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/chat"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
            >
              💬 Start Chatting
            </Link>
            <Link
              href="/chapters"
              className="inline-flex items-center px-6 py-3 border border-blue-600 text-base font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
              data-testid="choose-chapter"
            >
              📚 Choose Chapter
            </Link>
          </div>
        </div>
      </div>
    </main>
  )
}