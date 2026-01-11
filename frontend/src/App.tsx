import { ChatWindow } from './components/ChatWindow'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>CDD Docs Chat</h1>
        <p>Ask questions about CDD's architecture and features</p>
      </header>
      <ChatWindow />
    </div>
  )
}

export default App
