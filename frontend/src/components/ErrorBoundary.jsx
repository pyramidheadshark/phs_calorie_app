import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', height: '100dvh', padding: 32, textAlign: 'center',
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
          <p style={{ fontWeight: 700, fontSize: 18, marginBottom: 8 }}>Что-то пошло не так</p>
          <p style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 24 }}>
            {this.state.error.message || 'Неизвестная ошибка'}
          </p>
          <button
            className="btn btn-primary"
            onClick={() => this.setState({ error: null })}
          >
            Попробовать снова
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
