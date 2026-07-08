import { useState, useEffect, useRef } from 'react';
import { Header } from '@/components/Header';
import { PipelineBox } from '@/components/PipelineBox';
import { MailLists } from '@/components/MailLists';
import { ChatBox } from '@/components/ChatBox';
import { apiFetch } from '@/lib/api';
import type { Mail, Message } from '@/lib/api';

export function Dashboard() {
  const [linkedGoogleId, setLinkedGoogleId] = useState('');
  const [statusText, setStatusText] = useState('Status: Checking Google Mail authentication...');
  
  const [mails, setMails] = useState<Mail[]>([]);
  const [isSwarmRunning, setIsSwarmRunning] = useState(false);
  const [activeNodes, setActiveNodes] = useState<string[]>([]);
  const [routeBadge, setRouteBadge] = useState('Route: Collaborative LangGraph OS');
  const [isMailCollapsed, setIsMailCollapsed] = useState(false);
  const [isChatCollapsed, setIsChatCollapsed] = useState(false);
  const [chatMessages, setChatMessages] = useState<Message[]>([{
    id: 'welcome',
    role: 'ai',
    content: 'Welcome to your Copilot.\n\n**Authentication Required:** Please click **"Settings"** at the bottom left to securely connect your inbox.\n\nOnce signed in, click **"Run"** to analyze your emails.'
  }]);
  const [chatInput, setChatInput] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  useEffect(() => {
    checkGoogleStatus();
  }, []);

  async function checkGoogleStatus() {
    try {
      const res = await apiFetch('/api/accounts');
      const data = await res.json();
      
      if (data.accounts && data.accounts.length > 0) {
        setLinkedGoogleId(data.accounts[0].google_id);
        setStatusText(`Status: Idle. Google Mail linked (${data.accounts[0].email || data.accounts[0].google_id}). Click "Run Agentic Workflow" to triage inbox.`);
        fetchMails(data.accounts[0].google_id);
      } else {
        setLinkedGoogleId('');
        setStatusText('Status: Waiting for Google Mail sign-in. Please click "Sign in with Google Mail" above.');
      }
    } catch(e) {
      console.error('Error checking Google status:', e);
      setStatusText('Status: Connection Error');
    }
  }



  async function fetchMails(googleId: string) {
    if (!googleId) return;
    try {
      const mailRes = await apiFetch('/api/mails');
      const mailData = await mailRes.json();
      if (mailData.mails) {
        setMails(mailData.mails);
      }
    } catch(e) {
      console.error('Error fetching mails:', e);
    }
  }

  async function runLangGraph() {
    if (!linkedGoogleId) {
      alert('Please Sign in with Google Mail first before running the Agentic Workflow!');
      return;
    }
    
    setIsSwarmRunning(true);
    setActiveNodes(['fetch']);
    setStatusText('Status: [Agent 1] Authenticating with Google Gmail API...');

    try {
      setActiveNodes(['fetch', 'triage']);
      setStatusText(`Status: Connecting to live Gmail inbox for ${linkedGoogleId}...`);

      await apiFetch('/api/agent/run', {
        method: 'POST',
        body: JSON.stringify({google_id: linkedGoogleId})
      });

      setActiveNodes(['fetch', 'triage', 'analysis']);
      let currentMails: Mail[] = [];
      let stableCount = 0;
      let lastCount = -1;
      const maxAttempts = 72; // 6 mins
      
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise(r => setTimeout(r, 5000));
        
        const mailRes = await apiFetch('/api/mails');
        const mailData = await mailRes.json();
        currentMails = mailData.mails || [];
        setMails(currentMails);
        
        const secondsLeft = (maxAttempts - attempt) * 5;
        setStatusText(`Status: AI Swarm running... ${currentMails.length} emails classified so far (checking for more, ${secondsLeft}s remaining)`);
        
        if (currentMails.length > 0) {
          setActiveNodes(['fetch', 'triage', 'analysis', 'draft', 'brief']);
        }

        if (currentMails.length > 0 && currentMails.length === lastCount) {
          stableCount++;
          if (stableCount >= 2) break;
        } else {
          stableCount = 0;
        }
        lastCount = currentMails.length;
      }
      
      setStatusText('Status: Swarm Completed! Loaded ' + currentMails.length + ' live classified emails from Gmail.');
      setRouteBadge('Route: LIVE GMAIL INTEGRATION');

    } catch (err: any) {
      setStatusText('Error: ' + err.message);
    } finally {
      setIsSwarmRunning(false);
    }
  }

  async function sendChat() {
    const text = chatInput.trim();
    if (!text) return;
    
    if (!linkedGoogleId) {
      alert('Please Sign in with Google Mail first before using the Copilot!');
      return;
    }

    const newMessage: Message = { id: Date.now().toString() + '-user', role: 'user', content: text };
    setChatMessages(prev => [...prev, newMessage]);
    setChatInput('');

    const aiMessageId = Date.now().toString() + '-ai';
    setChatMessages(prev => [...prev, { id: aiMessageId, role: 'ai', content: 'Analyzing your inbox...' }]);

    try {
      const res = await apiFetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({query: text})
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      setChatMessages(prev => prev.map(m => m.id === aiMessageId ? {
        ...m,
        content: ''
      } : m));
      
      const reader = res.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      
      if (reader) {
        let currentMessageContent = "";
        let currentToolCalls: string[] = [];
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'message') {
                  currentMessageContent += data.content;
                } else if (data.type === 'tool_call') {
                  currentToolCalls = [...currentToolCalls, data.content];
                } else if (data.type === 'error') {
                  currentMessageContent += `\n\n⚠️ Error: ${data.content}\n\n`;
                }
                
                setChatMessages(prev => prev.map(m => m.id === aiMessageId ? {
                  ...m,
                  content: currentMessageContent || (currentToolCalls.length > 0 ? 'Using tools...' : 'Thinking...'),
                  toolCalls: currentToolCalls
                } : m));
              } catch (e) {
                // Ignore parse errors on incomplete chunks
              }
            }
          }
        }
      }
    } catch(e: any) {
      setChatMessages(prev => prev.map(m => m.id === aiMessageId ? {
        ...m,
        content: `Error connecting to Chat: ${e.message}`
      } : m));
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans overflow-x-hidden relative">
      <Header />
      
      <div className="mx-10 mt-8 mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Workflow</h2>
        </div>
        <button 
          disabled={isSwarmRunning} 
          onClick={runLangGraph} 
          className="bg-primary hover:bg-primary/90 text-primary-foreground h-10 px-6 rounded-md font-medium flex items-center gap-2 shadow-sm transition-all disabled:opacity-50"
        >
          {isSwarmRunning ? (
            <><span className="animate-pulse">●</span> Executing...</>
          ) : (
            <>Run Workflow</>
          )}
        </button>
      </div>

      <PipelineBox 
        routeBadge={routeBadge}
        activeNodes={activeNodes}
        statusText={statusText}
      />
      
      <div className="flex gap-8 p-4 px-10 pb-20 flex-1 min-h-[600px]">
        {/* Mail Container */}
        <div 
          className={`transition-all duration-300 flex flex-col relative ${
            isMailCollapsed ? 'w-12' : isChatCollapsed ? 'flex-1' : 'w-1/2'
          }`}
        >
          {!isMailCollapsed ? (
            <>
              <div className="absolute right-[-16px] top-4 z-10">
                <button onClick={() => setIsMailCollapsed(true)} className="bg-muted border border-border rounded-full p-1 hover:bg-muted/80 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                </button>
              </div>
              <MailLists mails={mails} />
            </>
          ) : (
            <div className="bg-card border border-border shadow-sm rounded-xl h-full flex flex-col items-center py-4 cursor-pointer hover:bg-accent/50" onClick={() => setIsMailCollapsed(false)}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              <span className="mt-4 font-semibold text-muted-foreground rotate-180" style={{ writingMode: 'vertical-rl' }}>Inbox</span>
            </div>
          )}
        </div>

        {/* Chat Container */}
        <div 
          className={`transition-all duration-300 flex flex-col relative ${
            isChatCollapsed ? 'w-12' : isMailCollapsed ? 'flex-1' : 'w-1/2'
          }`}
        >
          {!isChatCollapsed ? (
            <>
              <div className="absolute left-[-16px] top-4 z-10">
                <button onClick={() => setIsChatCollapsed(true)} className="bg-muted border border-border rounded-full p-1 hover:bg-muted/80 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </button>
              </div>
              <ChatBox 
                chatMessages={chatMessages}
                chatInput={chatInput}
                setChatInput={setChatInput}
                sendChat={sendChat}
                messagesEndRef={messagesEndRef}
              />
            </>
          ) : (
            <div className="bg-card border border-border shadow-sm rounded-xl h-[calc(100vh-180px)] sticky top-[100px] flex flex-col items-center py-4 cursor-pointer hover:bg-accent/50" onClick={() => setIsChatCollapsed(false)}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
              <span className="mt-4 font-semibold text-muted-foreground rotate-180" style={{ writingMode: 'vertical-rl' }}>Chat</span>
            </div>
          )}
        </div>
      </div>

      {/* Fixed Settings Button Bottom Left */}
      <a 
        href="/settings"
        className="fixed bottom-6 left-6 flex items-center gap-2 bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-full border border-border shadow-md transition-all text-sm font-medium z-50"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
        Settings
      </a>
    </div>
  );
}
