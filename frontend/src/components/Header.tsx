import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useTheme } from 'next-themes';
import { Moon, Sun, LogOut, Activity } from 'lucide-react';

export function Header() {
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  function handleLogout() {
    localStorage.removeItem('jwt_token');
    navigate('/login');
  }

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between p-4 px-8 bg-background/80 backdrop-blur-md border-b border-border shadow-sm">
      <div className="title-area">
        <h1 className="text-xl font-bold m-0 tracking-tight flex items-center gap-2">
          <Activity className="text-primary h-5 w-5" />
          <span className="bg-gradient-to-br from-foreground to-muted-foreground bg-clip-text text-transparent">Agentic Workspace</span>
        </h1>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} className="h-9 w-9 text-muted-foreground hover:text-foreground hover:bg-secondary">
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>

        <Button variant="ghost" size="sm" onClick={handleLogout} className="h-9 text-xs text-muted-foreground hover:text-destructive hover:bg-destructive/10">
          <LogOut size={14} className="mr-1" />
          <span className="hidden md:inline-block">Logout</span>
        </Button>
      </div>
    </header>
  );
}
