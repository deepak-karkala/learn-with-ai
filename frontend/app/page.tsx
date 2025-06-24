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
          <p className="text-sm text-gray-500">
            🚧 Under Development - Coming Soon
          </p>
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
    </main>
  )
}