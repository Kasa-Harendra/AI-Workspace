import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useGoogleLogin } from '@react-oauth/google';
import { apiFetch } from '@/lib/api';

interface Account {
  google_id: string;
  name: string;
  email: string;
}

export function Settings() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAccounts();
  }, []);

  async function fetchAccounts() {
    try {
      const res = await apiFetch('/api/accounts');
      if (res.status === 401) {
        navigate('/login');
        return;
      }
      const data = await res.json();
      if (data.accounts) {
        setAccounts(data.accounts);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const googleLogin = useGoogleLogin({
    flow: 'auth-code',
    scope: 'openid https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/calendar',
    onSuccess: async (tokenResponse) => {
      try {
        const res = await apiFetch('/api/auth/google', {
          method: 'POST',
          body: JSON.stringify({ 
            code: tokenResponse.code,
            redirect_uri: window.location.origin
          })
        });
        if (res.ok) {
          fetchAccounts();
        } else {
          const data = await res.json();
          alert('Error linking Google account: ' + (data.detail || data.message));
        }
      } catch (e: any) {
        alert('Error linking Google account: ' + e.message);
      }
    },
    onError: errorResponse => console.log(errorResponse),
  });

  async function removeAccount(googleId: string) {
    try {
      const res = await apiFetch(`/api/accounts/${googleId}`, { method: 'DELETE' });
      if (res.ok) {
        fetchAccounts();
      }
    } catch (e) {
      console.error(e);
    }
  }

  if (loading) {
    return <div className="min-h-screen bg-background p-10 text-foreground">Loading settings...</div>;
  }

  return (
    <div className="min-h-screen bg-background p-10">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8 border-b border-border pb-4">
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <Button variant="outline" onClick={() => navigate('/')} className="text-foreground border-border hover:bg-muted">
            &larr; Back to Dashboard
          </Button>
        </div>

        <Card className="bg-card border-border mb-8 shadow-sm">
          <CardHeader className="border-b border-border">
            <CardTitle className="text-xl text-card-foreground">Linked Google Accounts</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {accounts.length === 0 ? (
              <p className="text-muted-foreground mb-4">No Google accounts linked yet. You must link at least one account to run the Workflow.</p>
            ) : (
              <div className="flex flex-col gap-4 mb-6">
                {accounts.map(acc => (
                  <div key={acc.google_id} className="flex justify-between items-center p-4 border border-border rounded-lg bg-muted/50">
                    <div>
                      <div className="font-medium text-foreground">{acc.name}</div>
                      <div className="text-sm text-muted-foreground">{acc.email}</div>
                    </div>
                    <Button variant="destructive" onClick={() => removeAccount(acc.google_id)}>Remove</Button>
                  </div>
                ))}
              </div>
            )}

            <Button onClick={() => googleLogin()} className="bg-primary hover:bg-primary/90 text-primary-foreground flex items-center gap-2">
              <svg width="18" height="18" viewBox="0 0 24 24" className="bg-primary-foreground text-primary rounded-full p-0.5 fill-current"><path d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.4 1 3.5 3.6 1.6 7.4l3.7 2.8C6.2 7.3 8.9 5 12 5z"/><path d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"/><path d="M5.3 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.5.4-2.3L1.6 7.4C.6 9.4 0 11.6 0 14s.6 4.6 1.6 6.6l3.7-2.8z"/><path d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3.1 0-5.8-2.3-6.7-5.2L1.6 15.9C3.5 19.7 7.4 23 12 23z"/></svg>
              Link a Google Account
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
