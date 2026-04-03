const SUGGESTIONS = [
  "What is GitLab's mission?",
  "How does GitLab approach remote work?",
  "What is GitLab's product direction for AI?",
  "How does GitLab handle incident management?",
  "What are GitLab's company values?",
]

export default function SuggestedQuestions({ onSelect }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-gray-800 mb-2">GitLab Handbook Chatbot</h2>
      <p className="text-sm text-gray-500 mb-6 text-center max-w-md">
        Ask me anything about the GitLab Handbook and Direction pages. I'll find the most relevant information for you.
      </p>
      <div className="flex flex-wrap justify-center gap-2 max-w-lg">
        {SUGGESTIONS.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="text-sm bg-white border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 text-gray-700 hover:text-indigo-700 px-4 py-2 rounded-full transition-all shadow-sm"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
