import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  content: string
  className?: string
}

export default function MarkdownContent({ content, className = '' }: Props) {
  return (
    <div className={`markdown-body ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-lg font-bold text-slate-900 mt-4 mb-2 first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="text-base font-bold text-slate-900 mt-3 mb-2 first:mt-0">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold text-slate-800 mt-3 mb-1.5 first:mt-0">{children}</h3>,
          p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
          em: ({ children }) => <em className="italic text-slate-700">{children}</em>,
          ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          code: ({ className: cn, children }) =>
            cn ? (
              <code className="block bg-slate-900 text-slate-100 rounded-xl p-3 text-xs overflow-x-auto my-2">{children}</code>
            ) : (
              <code className="bg-slate-100 text-violet-700 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
            ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-violet-300 pl-3 my-2 text-slate-600 italic">{children}</blockquote>
          ),
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-violet-600 underline hover:text-violet-800">
              {children}
            </a>
          ),
          hr: () => <hr className="my-3 border-slate-200" />,
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full text-xs border border-slate-200 rounded-lg overflow-hidden">{children}</table>
            </div>
          ),
          th: ({ children }) => <th className="bg-slate-50 px-3 py-2 text-left font-semibold border-b">{children}</th>,
          td: ({ children }) => <td className="px-3 py-2 border-b border-slate-100">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
