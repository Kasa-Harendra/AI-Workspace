interface PipelineBoxProps {
  routeBadge: string;
  activeNodes: string[];
  statusText: string;
}

export function PipelineBox({ routeBadge, activeNodes, statusText }: PipelineBoxProps) {
  const nodes = [
    { id: 'fetch', title: 'Ingestion' },
    { id: 'triage', title: 'Triage' },
    { id: 'analysis', title: 'Analysis' },
    { id: 'draft', title: 'Drafting' },
    { id: 'brief', title: 'Synthesis' }
  ];

  return (
    <div className="mx-10 mt-8 mb-4 bg-card border border-border rounded-xl p-6 shadow-sm">
      <div className="flex justify-between items-center mb-5 text-sm font-medium text-muted-foreground uppercase tracking-wider">
        <span>Pipeline</span>
        <span className="font-normal">{routeBadge}</span>
      </div>
      <div className="flex items-center justify-between gap-2">
        {nodes.map((node, i) => (
          <div key={node.id} className="flex items-center flex-1">
            <div className={`flex-1 bg-muted/50 border border-border rounded-lg p-4 text-center transition-all duration-300 relative overflow-hidden ${activeNodes.includes(node.id) ? 'border-foreground shadow-sm bg-muted' : ''}`}>
              <div className="text-[13px] font-semibold text-foreground mb-1">{node.title}</div>
            </div>
            {i < 4 && <div className="text-muted-foreground/50 text-xl mx-2">&rarr;</div>}
          </div>
        ))}
      </div>
      <div className="mt-5 pt-4 border-t border-border flex justify-between items-center text-[13px] text-muted-foreground">
        <span>{statusText}</span>
      </div>
    </div>
  );
}
