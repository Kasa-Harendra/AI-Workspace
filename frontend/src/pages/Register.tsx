import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      
      if (res.ok && data.token) {
        localStorage.setItem('jwt_token', data.token);
        navigate('/');
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-card border-border shadow-sm">
        <CardHeader>
          <CardTitle className="text-2xl text-card-foreground text-center">Register</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleRegister} className="flex flex-col gap-4">
            {error && <div className="text-destructive text-sm font-medium">{error}</div>}
            <Input 
              placeholder="Username" 
              value={username} 
              onChange={e => setUsername(e.target.value)} 
              className="bg-muted/50 text-foreground border-border"
            />
            <Input 
              type="password"
              placeholder="Password" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              className="bg-muted/50 text-foreground border-border"
            />
            <Button type="submit" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">Create Account</Button>
            <div className="text-center text-sm text-muted-foreground mt-2">
              Already have an account? <Link to="/login" className="text-foreground hover:underline font-medium">Sign In</Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
