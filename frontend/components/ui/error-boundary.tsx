'use client'

import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <p className="text-white/40 text-sm">Something went wrong.</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-4 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-white/50 hover:text-white/70 transition-colors"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
