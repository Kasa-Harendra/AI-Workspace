import type { KeyboardEvent, RefObject } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { marked } from 'marked';
import { SendHorizontal, MessageSquare } from 'lucide-react';
import type { Message } from '@/lib/api';

interface ChatBoxProps {
  chatMessages: Message[];
  chatInput: string;
  setChatInput: (val: string) => void;
  sendChat: () => void;
  messagesEndRef: RefObject<HTMLDivElement | null>;
}

export function ChatBox({ chatMessages, chatInput, setChatInput, sendChat, messagesEndRef }: ChatBoxProps) {
  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      sendChat();
    }
  }

  return (
    <div className="bg-card border border-border rounded-xl flex flex-col h-[calc(100vh-180px)] sticky top-[100px] shadow-sm">
      <div className="p-5 border-b border-border font-semibold flex items-center justify-between">
        <span className="text-card-foreground flex items-center gap-2">
          <MessageSquare size={18} />
          Chat
        </span>
      </div>
      <ScrollArea className="flex-1 p-6">
        <div className="flex flex-col gap-4 mb-4">
          {chatMessages.map(msg => (
            <div 
              key={msg.id} 
              className={`max-w-[85%] p-4 rounded-lg text-sm leading-relaxed prose prose-sm dark:prose-invert ${
                msg.role === 'user' 
                  ? 'self-end bg-primary text-primary-foreground rounded-br-sm' 
                  : 'self-start bg-muted/50 border border-border text-foreground rounded-bl-sm'
              }`} 
            >
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <details className="mb-3 border border-border/50 rounded-md bg-background/30 overflow-hidden">
                  <summary className="cursor-pointer text-xs font-semibold text-muted-foreground px-3 py-2 select-none hover:bg-background/50 transition-colors flex items-center outline-none">
                    View Tool Calls ({msg.toolCalls.length})
                  </summary>
                  <div className="px-3 pb-3 space-y-2 mt-1">
                    {msg.toolCalls.map((tc, idx) => (
                      <div key={idx} className="text-xs font-mono text-muted-foreground bg-background/50 p-2 rounded whitespace-pre-wrap break-all border border-border/30">
                        {tc}
                      </div>
                    ))}
                  </div>
                </details>
              )}
              {msg.content && (
                <div dangerouslySetInnerHTML={{ __html: msg.role === 'ai' ? marked.parse(msg.content) : msg.content }} />
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      <div className="p-4 border-t border-border flex gap-3">
        <Input 
          value={chatInput}
          onChange={(e: any) => setChatInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-muted/50 border-border focus-visible:ring-primary text-foreground" 
          placeholder="Ask a question..." 
        />
        <Button onClick={sendChat} className="bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors">
          <SendHorizontal size={16} />
        </Button>
      </div>
    </div>
  );
}
