import ReactMarkdown from 'react-markdown'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Avatar + Name */}
        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold text-white ${
            isUser ? 'bg-indigo-500' : 'bg-orange-500'
          }`}>
            {isUser ? 'U' : 'G'}
          </div>
          <span className="text-xs text-gray-500 font-medium">
            {isUser ? 'You' : 'GitLab Bot'}
          </span>
        </div>

        {/* Message Bubble */}
        <div className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-indigo-500 text-white rounded-tr-sm'
            : message.isError
              ? 'bg-red-50 text-red-700 border border-red-200 rounded-tl-sm'
              : 'bg-white text-gray-800 border border-gray-200 rounded-tl-sm shadow-sm'
        }`}>
          {isUser ? (
            <p className="text-sm leading-relaxed">{message.content}</p>
          ) : (
            <div className="prose text-sm leading-relaxed">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 px-1">
            <p className="text-xs text-gray-400 font-medium mb-1">Sources:</p>
            <div className="flex flex-wrap gap-1.5">
              {message.sources.map((source, idx) => (
                <a
                  key={idx}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs bg-gray-100 hover:bg-indigo-50 text-gray-600 hover:text-indigo-600 px-2 py-1 rounded-full transition-colors border border-gray-200"
                  title={`Similarity: ${(source.similarity * 100).toFixed(0)}%`}
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  {source.title.length > 40 ? source.title.slice(0, 40) + '...' : source.title}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
