import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import type { Mail } from '@/lib/api';

interface MailListsProps {
  mails: Mail[];
}

const CATEGORIES = [
  { id: 'Recommended-next-actions', label: 'Next Actions' },
  { id: 'Upcoming-deadlines', label: 'Deadlines' },
  { id: 'Highest-priority-work', label: 'Priorities' },
  { id: 'Risks', label: 'Risks' },
  { id: 'Revenue-impacting-items', label: 'Revenue' },
  { id: 'Decisions-requiring-attention', label: 'Attention' },
  { id: 'Items-waiting-on-others', label: 'Waiting' },
];

export function MailLists({ mails }: MailListsProps) {
  if (mails.length === 0) {
    return (
      <div className="bg-card border border-border shadow-sm rounded-xl p-6 text-sm text-muted-foreground">
        Please run the Workflow to fetch your inbox.
      </div>
    );
  }

  return (
    <div className="bg-card border border-border shadow-sm rounded-xl p-2">
      <Accordion type="multiple" className="w-full" defaultValue={['Highest-priority-work', 'Recommended-next-actions']}>
        {CATEGORIES.map(category => {
          const categoryMails = mails.filter(m => m.category === category.id);
          if (categoryMails.length === 0) return null;

          return (
            <AccordionItem value={category.id} key={category.id} className="border-border px-4">
              <AccordionTrigger className="font-semibold hover:no-underline py-4 text-foreground">
                <div className="flex items-center gap-2">
                  {category.label}
                  <Badge variant="secondary" className="ml-2 text-xs h-5 px-1.5">{categoryMails.length}</Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent className="flex flex-col gap-3 pb-4">
                {categoryMails.map(m => (
                  <div key={m.mail_id} className="bg-muted/50 border border-border border-l-[3px] border-l-foreground rounded-lg p-4 flex justify-between items-start gap-4 transition-colors">
                    <div className="flex-1">
                      <div className="font-medium text-foreground">{m.subject || 'No Subject'}</div>
                      <div className="flex items-center gap-2 mt-1 mb-2">
                        <Badge variant="outline" className="text-[10px] tracking-wider flex items-center gap-1 bg-red-500/10 text-red-500 border-red-500/20">
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                          Gmail
                        </Badge>
                        <Badge variant="outline" className="text-[10px] tracking-wider lowercase bg-blue-500/10 text-blue-500 border-blue-500/20">{m.email || 'unknown@gmail.com'}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground/90 border-l-2 border-muted-foreground/20 pl-3 py-1 whitespace-pre-wrap">
                        {m.summary || m.snippet || ''}
                      </div>
                    </div>
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>
    </div>
  );
}
